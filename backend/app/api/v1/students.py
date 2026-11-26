from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, func
from typing import List, Optional
from pydantic import BaseModel
from app.core.database import get_session
from app.core.tenant import get_current_user, require_roles, get_department_details, get_tenant_drives
from app.models.entities import StudentProfile, User, Department, Application
from app.models.enums import UserRole
from app.services.eligibility_engine import AcademicSnapshot, compute_eligibility_dashboard

router = APIRouter(prefix="/students", tags=["Students"])


class UpdateProfileRequest(BaseModel):
    cgpa: Optional[float] = None
    standing_arrears: Optional[int] = None
    history_arrears: Optional[int] = None
    tenth_percentage: Optional[float] = None
    secondary_qualification_type: Optional[str] = None  # "HSC" | "DIPLOMA"
    twelfth_percentage: Optional[float] = None
    graduation_year: Optional[int] = None
    department_code: Optional[str] = None
    phone_number: Optional[str] = None
    bio: Optional[str] = None
    github_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    target_companies: Optional[str] = None
    target_min_ctc: Optional[float] = None


class EligibilityPreviewRequest(BaseModel):
    cgpa: Optional[float] = None
    standing_arrears: Optional[int] = None
    history_arrears: Optional[int] = None
    tenth_percentage: Optional[float] = None
    secondary_qualification_type: Optional[str] = None
    twelfth_percentage: Optional[float] = None
    department_code: Optional[str] = None
    target_companies: Optional[str] = None
    target_min_ctc: Optional[float] = None


def _validate_academic_bounds(
    cgpa: Optional[float],
    standing_arrears: int,
    history_arrears: int,
    tenth_percentage: Optional[float],
    twelfth_percentage: Optional[float],
    secondary_qualification_type: str,
    graduation_year: Optional[int] = None,
    target_min_ctc: Optional[float] = None,
) -> None:
    if cgpa is not None and (cgpa < 0.0 or cgpa > 10.0):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CGPA must be between 0.0 and 10.0")
    if standing_arrears < 0 or standing_arrears > 50:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Standing arrears must be between 0 and 50")
    if history_arrears < 0 or history_arrears > 50:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="History of arrears must be between 0 and 50")
    if history_arrears < standing_arrears:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"History of arrears ({history_arrears}) cannot be less than standing arrears ({standing_arrears})",
        )
    if tenth_percentage is not None and (tenth_percentage < 0.0 or tenth_percentage > 100.0):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="10th percentage must be between 0.0 and 100.0")
    if twelfth_percentage is not None and (twelfth_percentage < 0.0 or twelfth_percentage > 100.0):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="12th / Diploma percentage must be between 0.0 and 100.0")
    if secondary_qualification_type not in ("HSC", "DIPLOMA"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Secondary qualification type must be 'HSC' or 'DIPLOMA'",
        )
    if graduation_year is not None and (graduation_year < 2020 or graduation_year > 2035):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Graduation year must be between 2020 and 2035")
    if target_min_ctc is not None and (target_min_ctc < 0.0 or target_min_ctc > 500.0):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Minimum expected CTC must be between 0 and 500 LPA")


@router.get("/me")
def get_student_profile(
    current_user: User = Depends(require_roles([UserRole.STUDENT])),
    session: Session = Depends(get_session)
):
    student = session.exec(select(StudentProfile).where(StudentProfile.user_id == current_user.id)).first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found")

    dept_code, dept_name = get_department_details(session, student.department_id)
    apps_count = len(session.exec(select(Application).where(Application.student_id == student.id)).all())

    return {
        "profile": student,
        "department_name": dept_name,
        "department_code": dept_code,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "total_applications": apps_count
    }


@router.put("/me")
def update_student_profile(
    req: UpdateProfileRequest,
    current_user: User = Depends(require_roles([UserRole.STUDENT])),
    session: Session = Depends(get_session)
):
    student = session.exec(select(StudentProfile).where(StudentProfile.user_id == current_user.id)).first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found")

    eff_cgpa = req.cgpa if req.cgpa is not None else student.cgpa
    eff_standing = req.standing_arrears if req.standing_arrears is not None else student.standing_arrears
    if req.history_arrears is not None:
        eff_history = req.history_arrears
    else:
        eff_history = max(student.history_arrears, eff_standing)
    eff_tenth = req.tenth_percentage if req.tenth_percentage is not None else student.tenth_percentage
    eff_twelfth = req.twelfth_percentage if req.twelfth_percentage is not None else student.twelfth_percentage
    eff_qual = (
        req.secondary_qualification_type.strip().upper()
        if req.secondary_qualification_type is not None
        else (student.secondary_qualification_type or "HSC")
    )
    eff_grad = req.graduation_year if req.graduation_year is not None else student.graduation_year
    eff_ctc = req.target_min_ctc if req.target_min_ctc is not None else student.target_min_ctc

    _validate_academic_bounds(
        cgpa=eff_cgpa,
        standing_arrears=eff_standing,
        history_arrears=eff_history,
        tenth_percentage=eff_tenth,
        twelfth_percentage=eff_twelfth,
        secondary_qualification_type=eff_qual,
        graduation_year=eff_grad,
        target_min_ctc=eff_ctc,
    )

    if req.cgpa is not None:
        student.cgpa = round(req.cgpa, 2)
    if req.standing_arrears is not None:
        student.standing_arrears = req.standing_arrears
    if req.history_arrears is not None:
        student.history_arrears = req.history_arrears
    elif eff_history != student.history_arrears:
        student.history_arrears = eff_history
    if req.tenth_percentage is not None:
        student.tenth_percentage = round(req.tenth_percentage, 2)
    if req.twelfth_percentage is not None:
        student.twelfth_percentage = round(req.twelfth_percentage, 2)
    if req.secondary_qualification_type is not None:
        student.secondary_qualification_type = eff_qual
    if req.graduation_year is not None:
        student.graduation_year = req.graduation_year
    if req.department_code is not None and req.department_code.strip():
        dept = session.exec(
            select(Department).where(
                Department.college_id == student.college_id,
                func.upper(Department.code) == req.department_code.strip().upper(),
            )
        ).first()
        if dept:
            student.department_id = dept.id
    if req.phone_number is not None:
        student.phone_number = req.phone_number.strip()[:30]
    if req.bio is not None:
        student.bio = req.bio
    if req.github_url is not None:
        student.github_url = req.github_url.strip()[:250]
    if req.linkedin_url is not None:
        student.linkedin_url = req.linkedin_url.strip()[:250]
    if req.telegram_chat_id is not None:
        student.telegram_chat_id = req.telegram_chat_id.strip()[:100]
    if req.target_companies is not None:
        student.target_companies = req.target_companies.strip()[:500]
    if req.target_min_ctc is not None:
        student.target_min_ctc = round(req.target_min_ctc, 2)

    session.add(student)
    session.commit()
    session.refresh(student)

    dept_code, dept_name = get_department_details(session, student.department_id)
    drives = get_tenant_drives(session, student.college_id or current_user.college_id)
    eligibility = compute_eligibility_dashboard(student, dept_code, drives)

    return {
        "message": "Profile updated successfully",
        "profile": student,
        "department_code": dept_code,
        "department_name": dept_name,
        "eligibility": eligibility,
    }


@router.get("/me/eligibility")
def get_my_eligibility_dashboard(
    current_user: User = Depends(require_roles([UserRole.STUDENT])),
    session: Session = Depends(get_session)
):
    student = session.exec(select(StudentProfile).where(StudentProfile.user_id == current_user.id)).first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found")

    dept_code, dept_name = get_department_details(session, student.department_id)
    drives = get_tenant_drives(session, student.college_id or current_user.college_id)
    dashboard = compute_eligibility_dashboard(student, dept_code, drives)
    return {
        "department_code": dept_code,
        "department_name": dept_name,
        **dashboard,
    }


@router.post("/me/eligibility/preview")
def preview_eligibility(
    req: EligibilityPreviewRequest,
    current_user: User = Depends(require_roles([UserRole.STUDENT])),
    session: Session = Depends(get_session)
):
    student = session.exec(select(StudentProfile).where(StudentProfile.user_id == current_user.id)).first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found")

    eff_cgpa = req.cgpa if req.cgpa is not None else student.cgpa
    eff_standing = req.standing_arrears if req.standing_arrears is not None else student.standing_arrears
    if req.history_arrears is not None:
        eff_history = req.history_arrears
    else:
        eff_history = max(student.history_arrears, eff_standing)
    eff_tenth = req.tenth_percentage if req.tenth_percentage is not None else student.tenth_percentage
    eff_twelfth = req.twelfth_percentage if req.twelfth_percentage is not None else student.twelfth_percentage
    eff_qual = (
        req.secondary_qualification_type.strip().upper()
        if req.secondary_qualification_type is not None
        else (student.secondary_qualification_type or "HSC")
    )
    eff_ctc = req.target_min_ctc if req.target_min_ctc is not None else student.target_min_ctc

    _validate_academic_bounds(
        cgpa=eff_cgpa,
        standing_arrears=eff_standing,
        history_arrears=eff_history,
        tenth_percentage=eff_tenth,
        twelfth_percentage=eff_twelfth,
        secondary_qualification_type=eff_qual,
        target_min_ctc=eff_ctc,
    )

    saved_dept_code, _ = get_department_details(session, student.department_id)
    eff_dept = req.department_code.strip().upper() if req.department_code and req.department_code.strip() else saved_dept_code

    snapshot = AcademicSnapshot(
        cgpa=eff_cgpa,
        standing_arrears=eff_standing,
        history_arrears=eff_history,
        tenth_percentage=eff_tenth,
        secondary_qualification_type=eff_qual,
        twelfth_percentage=eff_twelfth,
        target_companies=req.target_companies if req.target_companies is not None else student.target_companies,
        target_min_ctc=eff_ctc,
    )
    drives = get_tenant_drives(session, student.college_id or current_user.college_id)
    return compute_eligibility_dashboard(snapshot, eff_dept, drives)


@router.get("/leaderboard")
def get_college_students_leaderboard(
    current_user: User = Depends(require_roles([UserRole.TPO, UserRole.COLLEGE_ADMIN, UserRole.ADMIN])),
    session: Session = Depends(get_session)
):
    query = select(StudentProfile)
    if current_user.college_id:
        query = query.where(StudentProfile.college_id == current_user.college_id)
        
    students = session.exec(query.order_by(StudentProfile.cgpa.desc())).all()

    results = []
    for s in students:
        user = session.get(User, s.user_id)
        dept = session.get(Department, s.department_id) if s.department_id else None
        results.append({
            "student_id": s.id,
            "name": user.full_name if user else "Student",
            "email": user.email if user else "",
            "roll_number": s.roll_number,
            "department": dept.code if dept else "N/A",
            "cgpa": s.cgpa,
            "standing_arrears": s.standing_arrears,
            "telegram_connected": bool(s.telegram_chat_id)
        })

    return results

