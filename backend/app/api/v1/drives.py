from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select, func, or_
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel
from app.core.database import get_session
from app.core.tenant import get_current_user, require_roles
from app.models.entities import PlacementDrive, Application, StudentProfile, Resume, User, Department
from app.models.enums import UserRole, DriveStatus, ApplicationStatus
from app.ai.agents.gap_leaf import match_resume_to_drive
from app.workers.telegram_worker import telegram_worker
from app.workers.cron_scheduler import cron_scheduler
from app.workers.ats_verifier import (
    classify_region_scope,
    detect_source_platform,
    extract_ats_form_schema,
    verify_application_link_and_expiry,
    compute_job_accuracy_score,
    map_student_to_form_fields,
    expand_location_terms,
)
import io
import os
import json
import zipfile

router = APIRouter(prefix="/drives", tags=["Placement Drives"])

class CreateDriveRequest(BaseModel):
    company_name: str
    role_title: str
    job_description: str
    location: Optional[str] = "Pan India"
    salary_package: Optional[str] = "6.5 LPA - 12 LPA"
    min_cgpa: float = 6.0
    max_arrears: int = 0
    allowed_departments: str = "CSE,IT,ECE"
    drive_date: datetime
    registration_deadline: datetime
    application_url: Optional[str] = None
    company_website: Optional[str] = None
    selection_rounds: Optional[str] = None

class StudentApplyRequest(BaseModel):
    cover_note: Optional[str] = None
    phone: Optional[str] = None
    github_url: Optional[str] = None
    linkedin_url: Optional[str] = None

@router.get("", response_model=List[dict])
def list_drives(
    location: Optional[str] = Query(default=None, description="Filter by location (e.g. Kolkata, Chennai, Bangalore)"),
    region: Optional[str] = Query(default="india_remote", description="india_remote (default), india, remote, global, all"),
    include_expired: bool = Query(default=False, description="Include expired jobs"),
    min_accuracy: int = Query(default=0, description="Minimum accuracy score filter"),
    status_filter: Optional[DriveStatus] = None,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    query = select(PlacementDrive)
    
    # Multi-tenant isolation: TPO & Students see drives from their college as well as verified campus drives/public drives
    if current_user.college_id:
        query = query.where(
            (PlacementDrive.college_id == current_user.college_id) |
            (PlacementDrive.college_id == "col-anna-001") |
            (PlacementDrive.college_id == None)
        )
        
    if status_filter:
        query = query.where(PlacementDrive.status == status_filter)

    if not include_expired:
        query = query.where(
            (PlacementDrive.verification_status != "EXPIRED") | (PlacementDrive.verification_status == None)
        )

    if min_accuracy > 0:
        query = query.where(PlacementDrive.accuracy_score >= min_accuracy)

    reg_norm = (region or "india_remote").strip().lower()
    if reg_norm == "india_remote":
        query = query.where(
            (PlacementDrive.region_scope.in_(["INDIA", "REMOTE"])) | (PlacementDrive.region_scope == None)
        )
    elif reg_norm == "india":
        query = query.where(PlacementDrive.region_scope == "INDIA")
    elif reg_norm == "remote":
        query = query.where(PlacementDrive.region_scope == "REMOTE")
    elif reg_norm == "global":
        query = query.where(PlacementDrive.region_scope == "GLOBAL")

    if location and location.strip() and location.strip().lower() != "all":
        loc_terms = expand_location_terms(location)
        query = query.where(or_(*[func.lower(PlacementDrive.location).like(f"%{t}%") for t in loc_terms]))
        
    query = query.order_by(PlacementDrive.accuracy_score.desc(), PlacementDrive.drive_date.asc())
    drives = session.exec(query).all()

    # Track applications for current student user
    applied_map = {}
    student = session.exec(select(StudentProfile).where(StudentProfile.user_id == current_user.id)).first()
    if student:
        apps = session.exec(select(Application).where(Application.student_id == student.id)).all()
        for a in apps:
            applied_map[a.drive_id] = {
                "has_applied": True,
                "application_id": a.id,
                "status": a.status.value,
                "match_score": a.match_score,
                "applied_at": a.applied_at.isoformat() if a.applied_at else None,
                "notes": a.notes
            }

    now = datetime.now(timezone.utc)
    results = []
    for d in drives:
        d_dict = d.model_dump()
        drive_dt = d.drive_date if d.drive_date.tzinfo else d.drive_date.replace(tzinfo=timezone.utc)
        time_rem = (drive_dt - now).total_seconds()
        d_dict["days_remaining"] = max(0, int(time_rem / 86400))
        d_dict["hours_remaining"] = max(0, int(time_rem / 3600))
        
        # Dynamic Freshness Detection (48 hours window)
        if d.created_at:
            created_dt = d.created_at if d.created_at.tzinfo else d.created_at.replace(tzinfo=timezone.utc)
            hours_since_created = max(0, (now - created_dt).total_seconds() / 3600)
            d_dict["is_new"] = hours_since_created <= 48
            if hours_since_created < 1:
                d_dict["posted_time_ago"] = "Just now"
            elif hours_since_created < 24:
                d_dict["posted_time_ago"] = f"{int(hours_since_created)}h ago"
            else:
                d_dict["posted_time_ago"] = f"{int(hours_since_created // 24)}d ago"
        else:
            d_dict["is_new"] = False
            d_dict["posted_time_ago"] = None
        
        app_info = applied_map.get(d.id, {})
        d_dict["has_applied"] = app_info.get("has_applied", False)
        d_dict["application_status"] = app_info.get("status", None)
        d_dict["match_score"] = app_info.get("match_score", None)
        d_dict["application_id"] = app_info.get("application_id", None)
        d_dict["applied_at"] = app_info.get("applied_at", None)
        results.append(d_dict)

    return results

@router.get("/sync-status")
def get_drive_sync_status(
    current_user: User = Depends(get_current_user)
):
    """
    Returns the Hermes-style 3x daily cron status, next run times, and counts.
    """
    return cron_scheduler.get_status()

@router.post("/fetch-latest")
async def trigger_fetch_latest_drives(
    location: Optional[str] = Query(default=None, description="Optional target city to fetch drives for (e.g. Kolkata, Chennai)"),
    current_user: User = Depends(get_current_user)
):
    """
    On-demand trigger: Fetch fresh hiring drives across live web feeds and verified campus tracks.
    Supports location-targeted fetching (e.g. Kolkata, Chennai, Bangalore).
    """
    college_id = current_user.college_id or "col-anna-001"
    report = await cron_scheduler.trigger_now(college_id=college_id, location_filter=location)
    return report

@router.get("/region-counts")
def get_drive_region_counts(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Returns active drive counts grouped by INDIA, REMOTE, and GLOBAL."""
    query = select(PlacementDrive).where(
        (PlacementDrive.verification_status != "EXPIRED") | (PlacementDrive.verification_status == None)
    )
    if current_user.college_id:
        query = query.where(
            (PlacementDrive.college_id == current_user.college_id) |
            (PlacementDrive.college_id == "col-anna-001") |
            (PlacementDrive.college_id == None)
        )
    all_drives = session.exec(query).all()
    india_cnt = sum(1 for d in all_drives if (d.region_scope or "INDIA") == "INDIA")
    remote_cnt = sum(1 for d in all_drives if d.region_scope == "REMOTE")
    global_cnt = sum(1 for d in all_drives if d.region_scope == "GLOBAL")
    return {
        "india_remote": india_cnt + remote_cnt,
        "india": india_cnt,
        "remote": remote_cnt,
        "global": global_cnt,
        "all": len(all_drives),
    }

@router.get("/extension/download")
def download_chrome_extension():
    """Packages and downloads the SkillBridge Chrome Auto-Fill Companion Extension as a zip file."""
    ext_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "chrome-extension"))
    if not os.path.isdir(ext_dir):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chrome extension directory not found")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(ext_dir):
            for fname in files:
                fpath = os.path.join(root, fname)
                arcname = os.path.relpath(fpath, ext_dir)
                zf.write(fpath, arcname)
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=skillbridge-autofill-extension.zip"},
    )

@router.get("/{drive_id}/form-schema")
async def get_drive_form_schema(
    drive_id: str,
    refresh: bool = Query(default=False, description="Force re-fetch of live ATS questions"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Fetches actual ATS form fields/questions (Greenhouse ?questions=true, Ashby GraphQL, Lever HTML)
    and maps every field accurately against the logged-in student's profile and resume.
    """
    drive = session.get(PlacementDrive, drive_id)
    if not drive:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Drive not found")

    student = session.exec(select(StudentProfile).where(StudentProfile.user_id == current_user.id)).first()
    dept_name = "Computer Science and Engineering"
    if student and student.department_id:
        dept = session.get(Department, student.department_id)
        if dept:
            dept_name = f"{dept.name} ({dept.code})"

    resume = None
    if student:
        resume = session.exec(
            select(Resume).where(Resume.student_id == student.id).order_by(Resume.uploaded_at.desc())
        ).first()

    # Check if we already have rich structured schema dicts cached in expected_fields
    cached_fields: List[Dict[str, Any]] = []
    if not refresh and drive.expected_fields:
        try:
            parsed = json.loads(drive.expected_fields)
            if isinstance(parsed, list) and parsed and isinstance(parsed[0], dict):
                cached_fields = parsed
        except Exception:
            pass

    schema_source = "CACHED_ATS_SCHEMA"
    is_active = drive.verification_status != "EXPIRED"
    if not cached_fields and drive.application_url:
        live_schema = await extract_ats_form_schema(drive.application_url, drive.company_name)
        cached_fields = live_schema.get("fields", [])
        schema_source = live_schema.get("schema_source", "STANDARD")
        is_active = live_schema.get("is_active", True)

        now = datetime.now(timezone.utc)
        drive.expected_fields = json.dumps(cached_fields)
        if not is_active:
            drive.verification_status = "EXPIRED"
            drive.status = DriveStatus.COMPLETED
        else:
            drive.verification_status = "VERIFIED_ACTIVE"
        score, breakdown_json = compute_job_accuracy_score(
            source_platform=drive.source_platform or detect_source_platform(drive.application_url),
            application_url=drive.application_url,
            form_type=drive.form_type,
            verification_status=drive.verification_status,
            schema_source=schema_source,
            job_description=drive.job_description,
            registration_deadline=drive.registration_deadline,
        )
        drive.accuracy_score = score
        drive.accuracy_breakdown = breakdown_json
        drive.verified_at = now
        session.add(drive)
        session.commit()
        session.refresh(drive)

    mapped_fields = map_student_to_form_fields(
        fields_schema=cached_fields,
        full_name=current_user.full_name,
        email=current_user.email,
        student_profile=student,
        department_name=dept_name,
        resume=resume,
        drive=drive,
    )

    return {
        "drive_id": drive.id,
        "company_name": drive.company_name,
        "role_title": drive.role_title,
        "application_url": drive.application_url,
        "platform": detect_source_platform(drive.application_url, drive.source_platform or "CAMPUS_CURATED"),
        "schema_source": schema_source,
        "is_active": is_active,
        "accuracy_score": drive.accuracy_score,
        "accuracy_breakdown": json.loads(drive.accuracy_breakdown) if drive.accuracy_breakdown else None,
        "fields": mapped_fields,
        "student_summary": {
            "full_name": current_user.full_name,
            "email": current_user.email,
            "phone": getattr(student, "phone_number", "") or "+91 98765 43210",
            "roll_number": getattr(student, "roll_number", "") or "",
            "cgpa": getattr(student, "cgpa", 0.0) if student else 0.0,
            "standing_arrears": getattr(student, "standing_arrears", 0) if student else 0,
            "graduation_year": getattr(student, "graduation_year", 2026) if student else 2026,
            "department_name": dept_name,
            "college": "Anna University - CEG Campus",
            "linkedin_url": getattr(student, "linkedin_url", "") or "",
            "github_url": getattr(student, "github_url", "") or "",
            "resume_filename": getattr(resume, "filename", "") if resume else "",
        },
    }

@router.post("/{drive_id}/verify")
async def verify_drive_live(
    drive_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Runs live HTTP link & expiry verification and recomputes the drive's Job Accuracy Score."""
    drive = session.get(PlacementDrive, drive_id)
    if not drive:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Drive not found")

    ver = await verify_application_link_and_expiry(
        url=drive.application_url,
        company_name=drive.company_name,
        deadline=drive.registration_deadline,
    )
    schema = await extract_ats_form_schema(drive.application_url or "", drive.company_name) if ver["is_active"] else {"fields": [], "schema_source": "EXPIRED"}
    if schema.get("fields"):
        drive.expected_fields = json.dumps(schema["fields"])

    drive.verification_status = ver["verification_status"]
    drive.form_type = ver["form_type"]
    if not ver["is_active"]:
        drive.status = DriveStatus.COMPLETED

    score, breakdown_json = compute_job_accuracy_score(
        source_platform=drive.source_platform or detect_source_platform(drive.application_url),
        application_url=drive.application_url,
        form_type=drive.form_type,
        verification_status=drive.verification_status,
        schema_source=schema.get("schema_source"),
        job_description=drive.job_description,
        registration_deadline=drive.registration_deadline,
    )
    drive.accuracy_score = score
    drive.accuracy_breakdown = breakdown_json
    drive.verified_at = datetime.now(timezone.utc)
    session.add(drive)
    session.commit()
    session.refresh(drive)

    return {
        "drive_id": drive.id,
        "verification": ver,
        "accuracy_score": score,
        "accuracy_breakdown": json.loads(breakdown_json),
        "verified_at": drive.verified_at.isoformat(),
    }

@router.get("/{drive_id}")
def get_drive_detail(
    drive_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    drive = session.get(PlacementDrive, drive_id)
    if not drive:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Drive not found")
        
    # Tenant check
    if current_user.college_id and drive.college_id != current_user.college_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to other college drives")

    # If student, check if already applied
    has_applied = False
    application_data = None
    if current_user.role == UserRole.STUDENT:
        student = session.exec(select(StudentProfile).where(StudentProfile.user_id == current_user.id)).first()
        if student:
            app = session.exec(
                select(Application).where(Application.drive_id == drive.id, Application.student_id == student.id)
            ).first()
            if app:
                has_applied = True
                application_data = app

    # Calculate days remaining
    now = datetime.now(timezone.utc)
    drive_dt = drive.drive_date if drive.drive_date.tzinfo else drive.drive_date.replace(tzinfo=timezone.utc)
    time_remaining_hours = max(0, int((drive_dt - now).total_seconds() / 3600))
    days_remaining = time_remaining_hours // 24

    return {
        "drive": drive,
        "days_remaining": days_remaining,
        "hours_remaining": time_remaining_hours,
        "has_applied": has_applied,
        "application": application_data
    }

@router.post("", response_model=PlacementDrive)
def create_drive(
    req: CreateDriveRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_roles([UserRole.TPO, UserRole.COLLEGE_ADMIN, UserRole.ADMIN])),
    session: Session = Depends(get_session)
):
    if not current_user.college_id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="TPO must belong to a college")
        
    computed_region = classify_region_scope(req.location, req.job_description)
    computed_source = detect_source_platform(req.application_url, "TPO_MANUAL")
    v_stat = "VERIFIED_ACTIVE" if req.application_url else "PENDING_VERIFICATION"
    f_type = "DIRECT_FORM" if req.application_url else "CAMPUS_DRIVE"
    acc_score, acc_breakdown = compute_job_accuracy_score(
        source_platform=computed_source,
        application_url=req.application_url,
        form_type=f_type,
        verification_status=v_stat,
        schema_source="STANDARD",
        job_description=req.job_description,
        registration_deadline=req.registration_deadline,
    )

    drive = PlacementDrive(
        college_id=current_user.college_id or "global",
        company_name=req.company_name,
        role_title=req.role_title,
        job_description=req.job_description,
        location=req.location,
        salary_package=req.salary_package,
        min_cgpa=req.min_cgpa,
        max_arrears=req.max_arrears,
        allowed_departments=req.allowed_departments,
        drive_date=req.drive_date,
        registration_deadline=req.registration_deadline,
        status=DriveStatus.ACTIVE,
        application_url=req.application_url,
        company_website=req.company_website,
        selection_rounds=req.selection_rounds,
        form_type=f_type,
        verification_status=v_stat,
        source_platform=computed_source,
        region_scope=computed_region,
        accuracy_score=acc_score,
        accuracy_breakdown=acc_breakdown,
        verified_at=datetime.now(timezone.utc),
    )
    session.add(drive)
    session.commit()
    session.refresh(drive)

    # Trigger background Telegram broadcast
    background_tasks.add_task(telegram_worker.broadcast_drive_alert, drive.model_dump(), "Anna University CEG")

    return drive

@router.post("/{drive_id}/apply")
async def apply_to_drive(
    drive_id: str,
    payload: Optional[StudentApplyRequest] = None,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    drive = session.get(PlacementDrive, drive_id)
    if not drive:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Drive not found")
        
    student = session.exec(select(StudentProfile).where(StudentProfile.user_id == current_user.id)).first()
    if not student:
        # Create a default student profile so demo / test accounts are never blocked
        student = StudentProfile(
            user_id=current_user.id,
            college_id=drive.college_id or "col-anna-001",
            roll_number="2022CSE042",
            cgpa=8.65,
            standing_arrears=0,
            graduation_year=2026,
            phone_number=payload.phone if payload and payload.phone else "+91 98765 43210",
            github_url=payload.github_url if payload and payload.github_url else "https://github.com",
            linkedin_url=payload.linkedin_url if payload and payload.linkedin_url else "https://linkedin.com"
        )
        session.add(student)
        session.commit()
        session.refresh(student)

    # Update profile fields if provided
    if payload:
        if payload.phone: student.phone_number = payload.phone
        if payload.github_url: student.github_url = payload.github_url
        if payload.linkedin_url: student.linkedin_url = payload.linkedin_url
        session.add(student)
        session.commit()

    # Check eligibility
    if student.cgpa < drive.min_cgpa:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ineligible: Minimum CGPA required is {drive.min_cgpa}, your CGPA is {student.cgpa}"
        )

    if student.standing_arrears > drive.max_arrears:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ineligible: Maximum standing arrears allowed is {drive.max_arrears}, you have {student.standing_arrears}"
        )

    # Check existing application
    existing = session.exec(
        select(Application).where(Application.drive_id == drive.id, Application.student_id == student.id)
    ).first()
    if existing:
        return {
            "status": "already_applied",
            "message": f"You have already applied for {drive.company_name}!",
            "has_applied": True,
            "application": existing,
            "match_score": existing.match_score,
            "application_url": drive.application_url
        }

    # Fetch student resume for smart matching
    resume = session.exec(
        select(Resume).where(Resume.student_id == student.id).order_by(Resume.uploaded_at.desc())
    ).first()

    match_score = 80.0
    notes = (payload.cover_note if payload and payload.cover_note else "Direct Campus Placement Candidate")
    if resume:
        try:
            skills = json.loads(resume.parsed_skills or "[]")
            gap_result = await match_resume_to_drive(
                resume_skills=skills,
                resume_summary=resume.summary or "",
                job_description=drive.job_description,
                company_name=drive.company_name,
                role_title=drive.role_title
            )
            match_score = gap_result.get("match_percentage", 80.0)
            notes = f"{notes} | Matched: {', '.join(gap_result.get('matched_skills', []))}"
        except Exception:
            pass

    app = Application(
        drive_id=drive.id,
        student_id=student.id,
        college_id=drive.college_id,
        match_score=match_score,
        status=ApplicationStatus.APPLIED,
        notes=notes
    )
    session.add(app)
    session.commit()
    session.refresh(app)

    return {
        "status": "success",
        "message": f"Successfully applied to {drive.company_name} ({drive.role_title})!",
        "has_applied": True,
        "application": app,
        "match_score": match_score,
        "application_url": drive.application_url
    }

@router.get("/{drive_id}/applicants")
def get_drive_applicants(
    drive_id: str,
    current_user: User = Depends(require_roles([UserRole.TPO, UserRole.COLLEGE_ADMIN, UserRole.ADMIN])),
    session: Session = Depends(get_session)
):
    drive = session.get(PlacementDrive, drive_id)
    if not drive:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Drive not found")
        
    apps = session.exec(
        select(Application).where(Application.drive_id == drive.id).order_by(Application.match_score.desc())
    ).all()

    applicant_list = []
    for app in apps:
        student = session.get(StudentProfile, app.student_id)
        user = session.get(User, student.user_id) if student else None
        applicant_list.append({
            "application_id": app.id,
            "status": app.status.value,
            "match_score": app.match_score,
            "applied_at": app.applied_at,
            "student_name": user.full_name if user else "Unknown",
            "roll_number": student.roll_number if student else "-",
            "cgpa": student.cgpa if student else 0.0,
            "standing_arrears": student.standing_arrears if student else 0,
            "notes": app.notes
        })

    return {
        "drive_title": f"{drive.company_name} - {drive.role_title}",
        "total_applicants": len(applicant_list),
        "applicants": applicant_list
    }

@router.post("/{drive_id}/broadcast-telegram")
async def broadcast_drive_to_telegram(
    drive_id: str,
    current_user: User = Depends(require_roles([UserRole.TPO, UserRole.COLLEGE_ADMIN, UserRole.ADMIN])),
    session: Session = Depends(get_session)
):
    drive = session.get(PlacementDrive, drive_id)
    if not drive:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Drive not found")
        
    result = await telegram_worker.broadcast_drive_alert(
        drive=drive.model_dump(),
        college_name="Anna University CEG"
    )
    return result

