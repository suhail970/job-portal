from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, func
from typing import List, Optional
from pydantic import BaseModel
from app.core.database import get_session
from app.core.tenant import get_current_user, require_roles, get_department_details
from app.models.entities import StudentProfile, User, Department, Application
from app.models.enums import UserRole

router = APIRouter(prefix="/students", tags=["Students"])

class UpdateProfileRequest(BaseModel):
    cgpa: Optional[float] = None
    standing_arrears: Optional[int] = None
    history_arrears: Optional[int] = None
    graduation_year: Optional[int] = None
    department_code: Optional[str] = None
    phone_number: Optional[str] = None
    bio: Optional[str] = None
    github_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    telegram_chat_id: Optional[str] = None

@router.get("/me")
def get_student_profile(
    current_user: User = Depends(require_roles([UserRole.STUDENT])),
    session: Session = Depends(get_session)
):
    student = session.exec(select(StudentProfile).where(StudentProfile.user_id == current_user.id)).first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found")

    dept_code, dept_name = get_department_details(session, student.department_id)

    # Applications count
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

    if req.cgpa is not None:
        if req.cgpa < 0.0 or req.cgpa > 10.0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CGPA must be between 0.0 and 10.0")
        student.cgpa = round(req.cgpa, 2)
    if req.standing_arrears is not None:
        if req.standing_arrears < 0 or req.standing_arrears > 50:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Standing arrears must be between 0 and 50")
        student.standing_arrears = req.standing_arrears
    if req.history_arrears is not None:
        if req.history_arrears < 0 or req.history_arrears > 50:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="History of arrears must be between 0 and 50")
        student.history_arrears = req.history_arrears
    if req.graduation_year is not None:
        if req.graduation_year < 2020 or req.graduation_year > 2035:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Graduation year must be between 2020 and 2035")
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
        student.phone_number = req.phone_number
    if req.bio is not None:
        student.bio = req.bio
    if req.github_url is not None:
        student.github_url = req.github_url
    if req.linkedin_url is not None:
        student.linkedin_url = req.linkedin_url
    if req.telegram_chat_id is not None:
        student.telegram_chat_id = req.telegram_chat_id

    session.add(student)
    session.commit()
    session.refresh(student)

    dept_code, dept_name = get_department_details(session, student.department_id)

    return {
        "message": "Profile updated successfully",
        "profile": student,
        "department_code": dept_code,
        "department_name": dept_name,
    }

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

