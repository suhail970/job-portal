from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List, Optional
from pydantic import BaseModel
from app.core.database import get_session
from app.core.tenant import get_current_user, require_roles
from app.models.entities import College, Department, User
from app.models.enums import UserRole

router = APIRouter(prefix="/colleges", tags=["Colleges & Departments"])

class CreateCollegeRequest(BaseModel):
    name: str
    code: str
    address: Optional[str] = None
    website: Optional[str] = None

class CreateDeptRequest(BaseModel):
    name: str
    code: str

@router.get("", response_model=List[College])
def list_colleges(session: Session = Depends(get_session)):
    return session.exec(select(College)).all()

@router.get("/{college_id}/departments", response_model=List[Department])
def list_departments(college_id: str, session: Session = Depends(get_session)):
    return session.exec(select(Department).where(Department.college_id == college_id)).all()

@router.post("", response_model=College)
def create_college(
    req: CreateCollegeRequest,
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    session: Session = Depends(get_session)
):
    existing = session.exec(select(College).where(College.code == req.code.strip())).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="College code already exists")
        
    college = College(
        name=req.name.strip(),
        code=req.code.strip(),
        address=req.address,
        website=req.website
    )
    session.add(college)
    session.commit()
    session.refresh(college)
    return college

@router.post("/{college_id}/departments", response_model=Department)
def add_department(
    college_id: str,
    req: CreateDeptRequest,
    current_user: User = Depends(require_roles([UserRole.COLLEGE_ADMIN, UserRole.TPO, UserRole.ADMIN])),
    session: Session = Depends(get_session)
):
    college = session.get(College, college_id)
    if not college:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="College not found")

    dept = Department(
        college_id=college_id,
        name=req.name.strip(),
        code=req.code.strip()
    )
    session.add(dept)
    session.commit()
    session.refresh(dept)
    return dept

