from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base

class ResearcherFeedback(Base):
    __tablename__ = "researcher_feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("exoplanet_candidates.id"), nullable=False)
    researcher_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Feedback timestamp
    feedback_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Feedback content
    agrees_with_ai = Column(Boolean, nullable=True)
    expert_classification = Column(String(50), nullable=False)  # "CONFIRMED", "FALSE_POSITIVE", "CANDIDATE"
    detailed_reasoning = Column(Text, nullable=False)
    supporting_data_references = Column(Text, nullable=True)  # URLs, paper citations, etc.
    
    # Confidence and methodology
    confidence_score = Column(Float, nullable=False)  # 0.0 to 1.0
    methodology_description = Column(Text, nullable=True)
    
    # Quality indicators
    feedback_weight = Column(Float, default=1.0)  # Based on researcher experience/reputation
    peer_review_status = Column(String(20), default="pending")  # pending, approved, disputed
    
    # Additional context
    time_spent_on_analysis = Column(Integer, nullable=True)  # minutes
    tools_used = Column(Text, nullable=True)  # List of analysis tools/software used
    
    # Relationships
    candidate = relationship("ExoplanetCandidate", back_populates="feedback_entries")
    researcher = relationship("User", back_populates="feedback_entries")
