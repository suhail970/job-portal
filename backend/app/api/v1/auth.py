from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from pydantic import BaseModel
from typing import Optional
from app.core.database import get_session
from app.core.security import verify_password, hash_password, create_access_token
from app.core.tenant import get_current_user, get_department_details
from app.models.entities import User, College, StudentProfile, Department
from app.models.enums import UserRole

router = APIRouter(prefix="/auth", tags=["Authentication"])

class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str
    role: UserRole = UserRole.STUDENT
    college_code: Optional[str] = None # e.g. "CEG-001"
    department_code: Optional[str] = "CSE"
    roll_number: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    full_name: str
    role: str
    college_id: Optional[str] = None

class LoginJsonRequest(BaseModel):
    email: str
    password: str

@router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == form_data.username.strip())).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user account")
    
    token = create_access_token(data={
        "sub": user.id,
        "email": user.email,
        "role": user.role.value,
        "college_id": user.college_id
    })
    
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role.value,
        college_id=user.college_id
    )

@router.post("/login-json", response_model=TokenResponse)
def login_json(req: LoginJsonRequest, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == req.email.strip())).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    
    token = create_access_token(data={
        "sub": user.id,
        "email": user.email,
        "role": user.role.value,
        "college_id": user.college_id
    })
    
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role.value,
        college_id=user.college_id
    )

@router.post("/register", response_model=TokenResponse)
def register(req: RegisterRequest, session: Session = Depends(get_session)):
    existing = session.exec(select(User).where(User.email == req.email.strip())).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    
    college_id = None
    if req.college_code:
        col = session.exec(select(College).where(College.code == req.college_code.strip())).first()
        if not col:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"College code '{req.college_code}' not found")
        college_id = col.id
        
    user = User(
        email=req.email.strip(),
        hashed_password=hash_password(req.password),
        full_name=req.full_name.strip(),
        role=req.role,
        college_id=college_id
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    # If student, create profile
    if req.role == UserRole.STUDENT and college_id:
        dept = None
        if req.department_code:
            dept = session.exec(
                select(Department).where(Department.college_id == college_id, Department.code == req.department_code)
            ).first()
            
        profile = StudentProfile(
            user_id=user.id,
            college_id=college_id,
            department_id=dept.id if dept else None,
            roll_number=req.roll_number or "2026STUDENT"
        )
        session.add(profile)
        session.commit()

    token = create_access_token(data={
        "sub": user.id,
        "email": user.email,
        "role": user.role.value,
        "college_id": user.college_id
    })

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role.value,
        college_id=user.college_id
    )

@router.get("/me")
def get_me(current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    college_name = None
    if current_user.college_id:
        col = session.get(College, current_user.college_id)
        if col:
            college_name = col.name
            
    student_profile = None
    department_code = None
    department_name = None
    if current_user.role == UserRole.STUDENT:
        student_profile = session.exec(
            select(StudentProfile).where(StudentProfile.user_id == current_user.id)
        ).first()
        if student_profile:
            department_code, department_name = get_department_details(session, student_profile.department_id)

    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role.value,
        "college_id": current_user.college_id,
        "college_name": college_name,
        "department_code": department_code,
        "department_name": department_name,
        "profile": student_profile
    }
