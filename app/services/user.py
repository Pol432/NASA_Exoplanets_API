from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import or_
from fastapi import HTTPException, status
from passlib.context import CryptContext
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from datetime import datetime

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserService:
    @staticmethod
    def get_password_hash(password: str) -> str:
        # Ensure password is within bcrypt's 72-byte limit
        # Encode to bytes first, then truncate, then decode back
        password_bytes = password.encode('utf-8')[:72]
        safe_password = password_bytes.decode('utf-8', errors='ignore')
        return pwd_context.hash(safe_password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        # Apply same truncation logic for verification
        password_bytes = plain_password.encode('utf-8')[:72]
        safe_password = password_bytes.decode('utf-8', errors='ignore')
        return pwd_context.verify(safe_password, hashed_password)
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        return db.query(User).filter(User.id == user_id, User.is_active == True).first()
    
    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        return db.query(User).filter(User.username == username, User.is_active == True).first()
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email, User.is_active == True).first()
    
    @staticmethod
    def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        return db.query(User).filter(User.is_active == True).offset(skip).limit(limit).all()
    
    @staticmethod
    def create_user(db: Session, user: UserCreate) -> User:
        # Check if user already exists
        existing_user = db.query(User).filter(
            or_(User.username == user.username, User.email == user.email)
        ).first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username or email already registered"
            )
        
        # Remove the manual truncation here since get_password_hash now handles it
        hashed_password = UserService.get_password_hash(user.password)
        db_user = User(
            username=user.username,
            email=user.email,
            hashed_password=hashed_password,
            role=user.role,
            full_name=user.full_name,
            research_specialization=user.research_specialization,
            organization_id=user.organization_id,
            bio=user.bio
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    
    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
        user = UserService.get_user_by_username(db, username)
        if not user:
            return None
        if not UserService.verify_password(password, user.hashed_password):
            return None
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()
        
        return user
    
    @staticmethod
    def update_user(db: Session, user_id: int, user_update: UserUpdate) -> User:
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        update_data = user_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        
        db.commit()
        db.refresh(user)
        return user
    
    @staticmethod
    def change_password(db: Session, user_id: int, old_password: str, new_password: str) -> None:
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if not UserService.verify_password(old_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect old password"
            )
        
        user.hashed_password = UserService.get_password_hash(new_password)
        db.commit()
    
    @staticmethod
    def delete_user(db: Session, user_id: int) -> None:
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user.is_active = False
        db.commit()
