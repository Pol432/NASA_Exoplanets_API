from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base

class AnalysisSession(Base):
    __tablename__ = "analysis_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("exoplanet_candidates.id"), nullable=False)
    researcher_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Session details
    session_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    time_spent_analyzing = Column(Integer, default=0)  # seconds
    
    # Analysis results
    researcher_verdict = Column(String(50), nullable=True)  # "CONFIRMED", "FALSE_POSITIVE", "CANDIDATE"
    confidence_level = Column(Float, nullable=True)  # 0.0 to 1.0
    methodology_used = Column(String(200), nullable=True)
    
    # Analysis details
    analysis_notes = Column(Text, nullable=True)
    key_observations = Column(Text, nullable=True)
    concerns_raised = Column(Text, nullable=True)
    
    # Session metadata
    session_completed = Column(Boolean, default=False)
    
    # Relationships
    candidate = relationship("ExoplanetCandidate", back_populates="analysis_sessions")
    researcher = relationship("User", back_populates="analysis_sessions")
