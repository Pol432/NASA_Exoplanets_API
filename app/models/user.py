from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base
import enum

class UserRole(str, enum.Enum):
    RESEARCHER = "researcher"
    ADMIN = "admin"
    MODERATOR = "moderator"

class VerificationStatus(str, enum.Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    # User profile
    role = Column(Enum(UserRole), default=UserRole.RESEARCHER, nullable=False)
    organization_id = Column(String(100), nullable=True)
    research_specialization = Column(String(100), nullable=True)
    verification_status = Column(Enum(VerificationStatus), default=VerificationStatus.PENDING)
    
    # Status and timestamps
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Additional profile fields
    full_name = Column(String(200), nullable=True)
    bio = Column(Text, nullable=True)
    
    # Relationships
    uploaded_candidates = relationship("ExoplanetCandidate", back_populates="uploader", cascade="all, delete-orphan")
    analysis_sessions = relationship("AnalysisSession", back_populates="researcher", cascade="all, delete-orphan")
    feedback_entries = relationship("ResearcherFeedback", back_populates="researcher", cascade="all, delete-orphan")
