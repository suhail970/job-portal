from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List, Optional
from pydantic import BaseModel
from app.core.database import get_session
from app.core.tenant import get_current_user, require_roles
from app.models.entities import StudentProfile, User, Department, Application
from app.models.enums import UserRole

router = APIRouter(prefix="/students", tags=["Students"])

class UpdateProfileRequest(BaseModel):
    cgpa: Optional[float] = None
    standing_arrears: Optional[int] = None
    history_arrears: Optional[int] = None
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

    dept_name = None
    if student.department_id:
        dept = session.get(Department, student.department_id)
        if dept:
            dept_name = f"{dept.name} ({dept.code})"

    # Applications count
    apps_count = len(session.exec(select(Application).where(Application.student_id == student.id)).all())

    return {
        "profile": student,
        "department_name": dept_name,
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
        student.cgpa = req.cgpa
    if req.standing_arrears is not None:
        student.standing_arrears = req.standing_arrears
    if req.history_arrears is not None:
        student.history_arrears = req.history_arrears
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
    return {"message": "Profile updated successfully", "profile": student}

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

