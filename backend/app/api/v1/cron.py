from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel
from croniter import croniter
import uuid
import logging

from app.core.database import get_session, engine
from app.core.tenant import get_current_user, require_roles
from app.models.entities import User, CronJob, CronExecution
from app.models.enums import UserRole
from app.workers.hermes_cron_engine import hermes_cron

logger = logging.getLogger("skillbridge.hermes_cron.api")

router = APIRouter(prefix="/cron", tags=["Hermes Cron Scheduler"])


class CreateCronJobRequest(BaseModel):
    name: str
    cron_expr: str
    target_location: Optional[str] = "All"
    description: Optional[str] = None
    grace_minutes: Optional[int] = 60


class UpdateCronJobRequest(BaseModel):
    name: Optional[str] = None
    cron_expr: Optional[str] = None
    target_location: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None
    grace_minutes: Optional[int] = None


@router.get("/status")
def get_cron_status(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Returns the Hermes-grade cron engine state, active slot schedule, and next upcoming run.
    """
    return hermes_cron.get_status()


@router.get("/jobs")
def list_cron_jobs(
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """
    Returns all registered Hermes cron jobs with their 5-field cron syntax, next run time, and last status.
    """
    return hermes_cron.list_jobs()


@router.post("/jobs", status_code=status.HTTP_201_CREATED)
def create_cron_job(
    payload: CreateCronJobRequest,
    current_user: User = Depends(require_roles([UserRole.TPO, UserRole.COLLEGE_ADMIN, UserRole.ADMIN])),
    session: Session = Depends(get_session)
):
    """
    Registers a new durable cron watchdog job into SQLite persistence.
    Validates standard 5-field cron syntax (e.g., '0 9 * * *') via croniter.
    """
    expr = payload.cron_expr.strip()
    if not croniter.is_valid(expr):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid 5-field cron syntax: '{expr}'. Expected standard syntax like '0 9 * * *' (min hour day-of-month month day-of-week)."
        )

    now = datetime.now(timezone.utc)
    try:
        next_run = hermes_cron.compute_next_run(expr, now)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to evaluate cron expression '{expr}': {str(e)}"
        )

    job = CronJob(
        id=f"cron-{uuid.uuid4().hex[:8]}",
        name=payload.name,
        cron_expr=expr,
        target_location=payload.target_location or "All",
        description=payload.description or f"Watcher for {payload.target_location or 'All'}",
        college_id=current_user.college_id,
        enabled=True,
        state="scheduled",
        next_run_at=next_run,
        grace_minutes=payload.grace_minutes if payload.grace_minutes is not None else 60,
        created_at=now
    )
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


@router.get("/jobs/{job_id}")
def get_cron_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Fetches full configuration of a specific cron job."""
    job = session.get(CronJob, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cron job not found")
    return job


@router.patch("/jobs/{job_id}")
def update_cron_job(
    job_id: str,
    payload: UpdateCronJobRequest,
    current_user: User = Depends(require_roles([UserRole.TPO, UserRole.COLLEGE_ADMIN, UserRole.ADMIN])),
    session: Session = Depends(get_session)
):
    """
    Updates cron job properties (e.g. toggle enabled/paused, modify cron expression, change target location).
    """
    job = session.get(CronJob, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cron job not found")

    if payload.cron_expr is not None:
        expr = payload.cron_expr.strip()
        if not croniter.is_valid(expr):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid 5-field cron syntax: '{expr}'"
            )
        job.cron_expr = expr
        job.next_run_at = hermes_cron.compute_next_run(expr)

    if payload.name is not None:
        job.name = payload.name.strip()
    if payload.target_location is not None:
        job.target_location = payload.target_location.strip()
    if payload.description is not None:
        job.description = payload.description.strip()
    if payload.grace_minutes is not None:
        job.grace_minutes = payload.grace_minutes

    if payload.enabled is not None:
        job.enabled = payload.enabled
        if not payload.enabled:
            job.state = "paused"
        else:
            job.state = "scheduled"
            job.next_run_at = hermes_cron.compute_next_run(job.cron_expr)

    session.add(job)
    session.commit()
    session.refresh(job)
    return job


@router.delete("/jobs/{job_id}")
def delete_cron_job(
    job_id: str,
    current_user: User = Depends(require_roles([UserRole.TPO, UserRole.COLLEGE_ADMIN, UserRole.ADMIN])),
    session: Session = Depends(get_session)
):
    """Deletes a custom cron job and its execution history."""
    job = session.get(CronJob, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cron job not found")

    # Cascade delete executions
    execs = session.exec(select(CronExecution).where(CronExecution.job_id == job_id)).all()
    for e in execs:
        session.delete(e)
    session.delete(job)
    session.commit()
    return {"status": "success", "message": f"Successfully deleted job {job_id}"}


@router.post("/jobs/{job_id}/run")
async def run_cron_job_now(
    job_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    On-Demand Execution: Instantly runs the specified cron job with atomic concurrency lock.
    Enforces Hermes [SILENT] quiet marker contract and records execution metrics to the durable ledger.
    """
    job = session.get(CronJob, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cron job not found")

    result = await hermes_cron.execute_job(job_id, dispatch_kind="manual")
    return result


@router.get("/jobs/{job_id}/history")
def get_job_history(
    job_id: str,
    limit: int = Query(default=15, le=100),
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """
    Returns the execution audit history for a cron job, including duration (ms),
    items added, and Hermes [SILENT] / ok / error status.
    """
    return hermes_cron.get_job_history(job_id, limit=limit)

