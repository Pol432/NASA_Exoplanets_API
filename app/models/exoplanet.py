from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base
import enum

class AnalysisStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"

class FinalVerdict(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FALSE_POSITIVE = "false_positive"
    CANDIDATE = "candidate"

class ExoplanetCandidate(Base):
    __tablename__ = "exoplanet_candidates"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # File and upload info
    original_csv_filename = Column(String(255), nullable=False)
    upload_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    researcher_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Analysis status
    analysis_status = Column(Enum(AnalysisStatus), default=AnalysisStatus.PENDING)
    final_verdict = Column(Enum(FinalVerdict), default=FinalVerdict.PENDING)
    consensus_score = Column(Float, default=0.0)
    discussion_thread_id = Column(String(100), nullable=True)
    
    # AI Predictions
    ai_prediction = Column(String(50), nullable=True)  # "CONFIRMED", "FALSE POSITIVE", "CANDIDATE"
    ai_confidence_score = Column(Float, nullable=True)
    
    # Kepler Dataset Columns - Core identification
    kepid = Column(Integer, nullable=True, index=True)
    kepoi_name = Column(String(20), nullable=True)
    kepler_name = Column(String(20), nullable=True)
    
    # Orbital parameters
    koi_period = Column(Float, nullable=True)
    koi_period_err1 = Column(Float, nullable=True)
    koi_period_err2 = Column(Float, nullable=True)
    koi_time0bk = Column(Float, nullable=True)
    koi_time0bk_err1 = Column(Float, nullable=True)
    koi_time0bk_err2 = Column(Float, nullable=True)
    
    # Transit parameters
    koi_impact = Column(Float, nullable=True)
    koi_impact_err1 = Column(Float, nullable=True)
    koi_impact_err2 = Column(Float, nullable=True)
    koi_duration = Column(Float, nullable=True)
    koi_duration_err1 = Column(Float, nullable=True)
    koi_duration_err2 = Column(Float, nullable=True)
    koi_depth = Column(Float, nullable=True)
    koi_depth_err1 = Column(Float, nullable=True)
    koi_depth_err2 = Column(Float, nullable=True)
    
    # Planet properties
    koi_prad = Column(Float, nullable=True)
    koi_prad_err1 = Column(Float, nullable=True)
    koi_prad_err2 = Column(Float, nullable=True)
    koi_teq = Column(Float, nullable=True)
    koi_teq_err1 = Column(Float, nullable=True)
    koi_teq_err2 = Column(Float, nullable=True)
    
    # Insolation flux
    koi_insol = Column(Float, nullable=True)
    koi_insol_err1 = Column(Float, nullable=True)
    koi_insol_err2 = Column(Float, nullable=True)
    
    # Model parameters
    koi_model_snr = Column(Float, nullable=True)
    koi_tce_plnt_num = Column(Integer, nullable=True)
    koi_steff = Column(Float, nullable=True)
    koi_steff_err1 = Column(Float, nullable=True)
    koi_steff_err2 = Column(Float, nullable=True)
    
    # Stellar parameters
    koi_slogg = Column(Float, nullable=True)
    koi_slogg_err1 = Column(Float, nullable=True)
    koi_slogg_err2 = Column(Float, nullable=True)
    koi_srad = Column(Float, nullable=True)
    koi_srad_err1 = Column(Float, nullable=True)
    koi_srad_err2 = Column(Float, nullable=True)
    
    # RA/Dec coordinates
    ra = Column(Float, nullable=True)
    dec = Column(Float, nullable=True)
    koi_kepmag = Column(Float, nullable=True)
    
    # Disposition and scores
    koi_disposition = Column(String(20), nullable=True)
    koi_pdisposition = Column(String(20), nullable=True)
    koi_score = Column(Float, nullable=True)
    
    # Additional analysis fields
    analysis_notes = Column(Text, nullable=True)
    quality_flags = Column(Text, nullable=True)  # JSON string of quality indicators
    
    # Relationships
    uploader = relationship("User", back_populates="uploaded_candidates")
    analysis_sessions = relationship("AnalysisSession", back_populates="candidate", cascade="all, delete-orphan")
    feedback_entries = relationship("ResearcherFeedback", back_populates="candidate", cascade="all, delete-orphan")
