from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime
from app.models.user import UserRole, VerificationStatus

class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    research_specialization: Optional[str] = None
    organization_id: Optional[str] = None
    bio: Optional[str] = None

class UserCreate(UserBase):
    password: str
    role: Optional[UserRole] = UserRole.RESEARCHER
    
    @validator('username')
    def username_alphanumeric(cls, v):
        assert v.isalnum(), 'Username must be alphanumeric'
        return v

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    research_specialization: Optional[str] = None
    organization_id: Optional[str] = None
    bio: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(UserBase):
    id: int
    role: UserRole
    verification_status: VerificationStatus
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        orm_mode = True

class UserPublic(BaseModel):
    id: int
    username: str
    full_name: Optional[str] = None
    research_specialization: Optional[str] = None
    verification_status: VerificationStatus
    created_at: datetime
    
    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class PasswordChange(BaseModel):
    old_password: str
    new_password: str
    
    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v
