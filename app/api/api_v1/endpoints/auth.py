from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.schemas.user import (
    UserCreate, UserUpdate, UserResponse, UserPublic, 
    PasswordChange, UserLogin, Token
)
from app.services.user import UserService
from app.services.auth import get_current_active_user, AuthService
from app.models.user import User
from datetime import timedelta
from app.core.config import settings

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    return UserService.create_user(db=db, user=user)

@router.post("/login", response_model=Token)
def login_user(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """Login user and return access token"""
    user = UserService.authenticate_user(
        db, user_credentials.username, user_credentials.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = AuthService.create_access_token(
        user=user, 
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_active_user)):
    """Get current user's profile"""
    return current_user

@router.put("/me", response_model=UserResponse)
def update_current_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update current user's profile"""
    return UserService.update_user(db=db, user_id=current_user.id, user_update=user_update)

@router.post("/me/change-password", status_code=status.HTTP_200_OK)
def change_password(
    password_change: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Change current user's password"""
    UserService.change_password(
        db=db,
        user_id=current_user.id,
        old_password=password_change.old_password,
        new_password=password_change.new_password
    )
    return {"message": "Password changed successfully"}

@router.delete("/me", status_code=status.HTTP_200_OK)
def delete_current_user_account(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete current user's account (soft delete)"""
    UserService.delete_user(db=db, user_id=current_user.id)
    return {"message": "Account deleted successfully"}

@router.get("/users", response_model=List[UserPublic])
def get_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get list of users (public information only)"""
    users = UserService.get_users(db, skip=skip, limit=limit)
    return users

@router.get("/users/{user_id}", response_model=UserPublic)
def get_user_by_id(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user by ID (public information only)"""
    user = UserService.get_user_by_id(db, user_id=user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user
