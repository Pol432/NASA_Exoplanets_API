from datetime import timedelta
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.user import UserService
from app.models.user import User
from auth_shared.jwt import JWTAuth

# Security scheme
security = HTTPBearer()

class AuthService:
    @staticmethod
    def create_access_token(user: User, expires_delta: timedelta):
        payload = {
            "user_id": user.id,
            "username": user.username,
            "role": user.role.value
        }
        token = JWTAuth.create_access_token(payload, expires_delta)
        return token

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = credentials.credentials
    try:
        payload = JWTAuth.verify_token(token)
        user_id = payload.get("user_id")
        
        if user_id is None:
            raise credentials_exception
        
        user = UserService.get_user_by_id(db, user_id=user_id)
        if user is None:
            raise credentials_exception
        
        return user
    except Exception:
        raise credentials_exception

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Inactive user"
        )
    return current_user

def require_role(required_role: str):
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role.value != required_role and current_user.role.value != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return current_user
    return role_checker
