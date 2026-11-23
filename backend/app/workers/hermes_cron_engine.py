import asyncio
import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from croniter import croniter
from sqlmodel import Session, select, func
from app.core.database import engine
from app.models.entities import CronJob, CronExecution, PlacementDrive
from app.workers.job_fetcher import job_fetcher
from app.workers.telegram_worker import telegram_worker

logger = logging.getLogger("skillbridge.hermes_cron")

class HermesCronEngine:
    """
    Hermes Agent Parity Cron Subsystem.
    Features:
      - 5-field standard cron expressions evaluated via croniter
      - Durable SQLite state persistence across all server reboots
      - Missed-occurrence contract (late vs catch-up grace handling)
      - Atomic concurrency locks per job (prevents overlapping runs)
      - [SILENT] quiet marker protocol (avoids spam when 0 new items found)
      - Detailed execution history & duration tracking (ms)
    """

    def __init__(self):
        self.is_running: bool = False
        self._loop_task: Optional[asyncio.Task] = None
        self._job_locks: Dict[str, asyncio.Lock] = {}
        self._global_lock = asyncio.Lock()

    def _get_job_lock(self, job_id: str) -> asyncio.Lock:
        if job_id not in self._job_locks:
            self._job_locks[job_id] = asyncio.Lock()
        return self._job_locks[job_id]

    @staticmethod
    def compute_next_run(cron_expr: str, base_time: Optional[datetime] = None) -> datetime:
        """Computes the exact next firing timestamp using croniter."""
        now = base_time or datetime.now(timezone.utc)
        # Ensure aware UTC datetime
        if not now.tzinfo:
            now = now.replace(tzinfo=timezone.utc)
        iter = croniter(cron_expr, now)
        next_dt = iter.get_next(datetime)
        if not next_dt.tzinfo:
            next_dt = next_dt.replace(tzinfo=timezone.utc)
        return next_dt

    @staticmethod
    def format_countdown(target_time: datetime) -> str:
        """Formats countdown in clean human readable notation."""
        now = datetime.now(timezone.utc)
        if not target_time.tzinfo:
            target_time = target_time.replace(tzinfo=timezone.utc)
        diff = target_time - now
        total_seconds = max(0, int(diff.total_seconds()))
        hours, remainder = divmod(total_seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        if hours > 24:
            days = hours // 24
            return f"{days}d {hours % 24}h"
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"

    async def execute_job(self, job_id: str, dispatch_kind: str = "scheduled") -> Dict[str, Any]:
        """
        Executes a single cron job with concurrency lock and execution logging.
        Implements the Hermes [SILENT] quiet marker contract.
        """
        lock = self._get_job_lock(job_id)
        if lock.locked():
            logger.warning(f"Job {job_id} is already executing. Rejecting overlapping run.")
            return {"status": "locked", "message": "Job is already running"}

        async with lock:
            start_wall = time.perf_counter()
            start_dt = datetime.now(timezone.utc)
            
            with Session(engine) as session:
                job = session.get(CronJob, job_id)
                if not job:
                    return {"status": "not_found", "message": f"Job {job_id} does not exist"}

                job_name = job.name
                job_college_id = job.college_id
                job_target_location = job.target_location
                job_cron_expr = job.cron_expr

                # Mark job as running in DB
                job.state = "running"
                session.add(job)
                
                # Create execution ledger entry
                execution = CronExecution(
                    job_id=job.id,
                    dispatch_kind=dispatch_kind,
                    started_at=start_dt,
                    status="running"
                )
                session.add(execution)
                session.commit()
                exec_id = execution.id

            # Resolve actual college_id to active tenant
            resolved_college_id = job_college_id
            if not resolved_college_id or resolved_college_id == "col-anna-001":
                with Session(engine) as session:
                    col = session.exec(select(College)).first()
                    resolved_college_id = col.id if col else "col-anna-001"

            # Perform the actual ingestion
            error_msg: Optional[str] = None
            ingestion_report: Dict[str, Any] = {}
            try:
                ingestion_report = await job_fetcher.run_ingestion(
                    college_id=resolved_college_id,
                    location_filter=job_target_location
                )
            except Exception as e:
                logger.error(f"Execution failed for job '{job_name}': {e}", exc_info=True)
                error_msg = str(e)

            duration_ms = int((time.perf_counter() - start_wall) * 1000)
            finish_dt = datetime.now(timezone.utc)
            new_added = ingestion_report.get("new_drives_added", 0) if not error_msg else 0

            # Determine final status using Hermes [SILENT] contract
            if error_msg:
                final_status = "error"
                summary = f"Execution failed: {error_msg}"
            elif new_added == 0:
                final_status = "silent" # Hermes Quiet Marker: Evaluated OK, no new items discovered
                tot_active = ingestion_report.get("total_active_drives", 0)
                loc_name = ingestion_report.get("location_filtered", "all tech hubs")
                summary = f"Evaluated {ingestion_report.get('total_candidates_evaluated', 0)} candidates. All {tot_active} drives in {loc_name} up-to-date [SILENT]."
            else:
                final_status = "ok"
                comps = ingestion_report.get("companies_added", [])
                tot_active = ingestion_report.get("total_active_drives", 0)
                loc_name = ingestion_report.get("location_filtered", "all tech hubs")
                summary = f"Added {new_added} new drives ({', '.join(comps[:3])}{'...' if len(comps) > 3 else ''}). Now {tot_active} active in {loc_name}."
                # Broadcast alert for new drives
                try:
                    await telegram_worker.broadcast_drive_alert(
                        drive={"company_name": comps[0], "role_title": "Campus Opportunities"},
                        college_name="Anna University CEG"
                    )
                except Exception as tg_err:
                    logger.warning(f"Telegram notice failed: {tg_err}")

            # Update DB records atomically
            next_run_iso: Optional[str] = None
            with Session(engine) as session:
                job_rec = session.get(CronJob, job_id)
                exec_rec = session.get(CronExecution, exec_id)
                if exec_rec:
                    exec_rec.finished_at = finish_dt
                    exec_rec.duration_ms = duration_ms
                    exec_rec.status = final_status
                    exec_rec.new_drives_added = new_added
                    exec_rec.summary = summary
                    exec_rec.error_message = error_msg
                    session.add(exec_rec)

                if job_rec:
                    job_rec.last_run_at = finish_dt
                    job_rec.last_status = final_status
                    job_rec.last_error = error_msg
                    job_rec.total_runs += 1
                    job_rec.state = "scheduled" if job_rec.enabled else "paused"
                    # Advance to next scheduled slot
                    job_rec.next_run_at = self.compute_next_run(job_rec.cron_expr, finish_dt)
                    next_run_iso = job_rec.next_run_at.isoformat()
                    session.add(job_rec)

                session.commit()

            logger.info(f"Cron Job '{job_name}' finished [{final_status}] in {duration_ms}ms. Next run: {next_run_iso}")

            return {
                "status": "success" if not error_msg else "error",
                "final_status": final_status,
                "job_name": job_name,
                "duration_ms": duration_ms,
                "new_drives_added": new_added,
                "companies_added": ingestion_report.get("companies_added", []),
                "total_candidates_evaluated": ingestion_report.get("total_candidates_evaluated", 0),
                "summary": summary,
                "next_run_at": next_run_iso
            }

    async def _evaluate_due_jobs(self):
        """
        Hermes Due-Job Evaluator & Missed-Occurrence Contract.
        Scans for due jobs and handles restart gaps (late vs catch-up).
        """
        now = datetime.now(timezone.utc)
        due_jobs: List[tuple] = [] # (job_id, dispatch_kind)

        with Session(engine) as session:
            jobs = session.exec(
                select(CronJob).where(
                    CronJob.enabled == True,
                    CronJob.state != "running",
                    CronJob.state != "paused"
                )
            ).all()

            for j in jobs:
                next_run = j.next_run_at
                if not next_run.tzinfo:
                    next_run = next_run.replace(tzinfo=timezone.utc)

                if next_run <= now:
                    diff_mins = (now - next_run).total_seconds() / 60.0
                    grace = j.grace_minutes or 60
                    if diff_mins <= grace:
                        # Slot is slightly late within grace period
                        dispatch_kind = "late" if diff_mins > 5 else "scheduled"
                    else:
                        # Past grace window: collapse backlog, fire once as catch_up
                        dispatch_kind = "catch_up"
                        logger.warning(f"Job '{j.name}' was overdue by {int(diff_mins)}m (past grace of {grace}m). Triggering catch_up run.")
                    
                    due_jobs.append((j.id, dispatch_kind))

        # Execute due jobs
        for job_id, dispatch_kind in due_jobs:
            asyncio.create_task(self.execute_job(job_id, dispatch_kind=dispatch_kind))

    async def _scheduler_loop(self):
        logger.info("Hermes-grade Cron Engine started. Ticking every 15 seconds.")
        self.is_running = True
        
        while self.is_running:
            try:
                await self._evaluate_due_jobs()
                await asyncio.sleep(15)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in Hermes cron engine tick: {e}", exc_info=True)
                await asyncio.sleep(15)

    def start(self):
        if not self.is_running or self._loop_task is None:
            self._loop_task = asyncio.create_task(self._scheduler_loop())

    def stop(self):
        self.is_running = False
        if self._loop_task and not self._loop_task.done():
            self._loop_task.cancel()

    # -------------------------------------------------------------
    # Management & Status Helpers
    # -------------------------------------------------------------
    def list_jobs(self) -> List[Dict[str, Any]]:
        with Session(engine) as session:
            jobs = session.exec(select(CronJob).order_by(CronJob.created_at.asc())).all()
            output = []
            for j in jobs:
                output.append({
                    "id": j.id,
                    "name": j.name,
                    "description": j.description,
                    "cron_expr": j.cron_expr,
                    "target_location": j.target_location or "All",
                    "enabled": j.enabled,
                    "state": j.state,
                    "next_run_at": j.next_run_at.isoformat(),
                    "countdown": self.format_countdown(j.next_run_at),
                    "last_run_at": j.last_run_at.isoformat() if j.last_run_at else None,
                    "last_status": j.last_status,
                    "total_runs": j.total_runs,
                    "grace_minutes": j.grace_minutes
                })
            return output

    def get_job_history(self, job_id: str, limit: int = 15) -> List[Dict[str, Any]]:
        with Session(engine) as session:
            execs = session.exec(
                select(CronExecution)
                .where(CronExecution.job_id == job_id)
                .order_by(CronExecution.started_at.desc())
                .limit(limit)
            ).all()
            return [
                {
                    "id": e.id,
                    "dispatch_kind": e.dispatch_kind,
                    "started_at": e.started_at.isoformat(),
                    "finished_at": e.finished_at.isoformat() if e.finished_at else None,
                    "duration_ms": e.duration_ms,
                    "status": e.status,
                    "new_drives_added": e.new_drives_added,
                    "summary": e.summary,
                    "error_message": e.error_message
                }
                for e in execs
            ]

    # Backward compatibility with existing cron_scheduler interface
    def get_status(self) -> Dict[str, Any]:
        with Session(engine) as session:
            total_drives = session.exec(select(func.count(PlacementDrive.id))).one()
            all_jobs = self.list_jobs()

        next_job = min(all_jobs, key=lambda x: x["next_run_at"]) if all_jobs else None
        return {
            "status": "active" if self.is_running else "idle",
            "schedule": "Hermes-grade Cron (Standard 5-Field Syntax via croniter)",
            "jobs_count": len(all_jobs),
            "jobs": all_jobs,
            "slots": all_jobs,
            "next_run": {
                "slot_name": next_job["name"] if next_job else "None",
                "scheduled_time": next_job["cron_expr"] if next_job else "-",
                "countdown": next_job["countdown"] if next_job else "-",
                "next_run_iso": next_job["next_run_at"] if next_job else None
            } if next_job else None,
            "total_active_drives": total_drives
        }

    async def trigger_now(self, college_id: Optional[str] = None, location_filter: Optional[str] = None) -> Dict[str, Any]:
        """Manual trigger helper: fetches live openings for specified college and location."""
        effective_college_id = college_id
        if not effective_college_id or effective_college_id == "col-anna-001":
            with Session(engine) as session:
                col = session.exec(select(College)).first()
                effective_college_id = col.id if col else "col-anna-001"

        return await job_fetcher.run_ingestion(college_id=effective_college_id, location_filter=location_filter)

hermes_cron = HermesCronEngine()
# Backward compatibility alias
cron_scheduler = hermes_cron
