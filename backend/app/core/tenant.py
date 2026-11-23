from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select
from typing import List, Optional
from app.core.database import get_session
from app.core.security import decode_access_token
from app.models.entities import User
from app.models.enums import UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials or token expired",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
        
    user_id: Optional[str] = payload.get("sub")
    if user_id is None:
        raise credentials_exception
        
    user = session.get(User, user_id)
    if user is None or not user.is_active:
        raise credentials_exception
        
    return user

def require_roles(allowed_roles: List[UserRole]):
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles and current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Requires one of roles: {[r.value for r in allowed_roles]}"
            )
        return current_user
    return role_checker

def get_current_tenant_id(current_user: User = Depends(get_current_user)) -> Optional[str]:
    """
    Returns the college_id of the current user.
    Admins can act across colleges, while TPO and Students are strictly bound to their college_id.
    """
    if current_user.role == UserRole.ADMIN:
        return current_user.college_id # Can be None for global view
        
    if not current_user.college_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not associated with any college tenant"
        )
    return current_user.college_id

