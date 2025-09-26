from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime
from app.models.exoplanet import AnalysisStatus, FinalVerdict

class ExoplanetCandidateBase(BaseModel):
    original_csv_filename: str
    
    # Kepler dataset fields - all optional as they might not be present
    kepid: Optional[int] = None
    kepoi_name: Optional[str] = None
    kepler_name: Optional[str] = None
    
    # Orbital parameters
    koi_period: Optional[float] = None
    koi_period_err1: Optional[float] = None
    koi_period_err2: Optional[float] = None
    koi_time0bk: Optional[float] = None
    koi_time0bk_err1: Optional[float] = None
    koi_time0bk_err2: Optional[float] = None
    
    # Transit parameters
    koi_impact: Optional[float] = None
    koi_impact_err1: Optional[float] = None
    koi_impact_err2: Optional[float] = None
    koi_duration: Optional[float] = None
    koi_duration_err1: Optional[float] = None
    koi_duration_err2: Optional[float] = None
    koi_depth: Optional[float] = None
    koi_depth_err1: Optional[float] = None
    koi_depth_err2: Optional[float] = None
    
    # Planet properties
    koi_prad: Optional[float] = None
    koi_prad_err1: Optional[float] = None
    koi_prad_err2: Optional[float] = None
    koi_teq: Optional[float] = None
    koi_teq_err1: Optional[float] = None
    koi_teq_err2: Optional[float] = None
    
    # Insolation flux
    koi_insol: Optional[float] = None
    koi_insol_err1: Optional[float] = None
    koi_insol_err2: Optional[float] = None
    
    # Model and stellar parameters
    koi_model_snr: Optional[float] = None
    koi_tce_plnt_num: Optional[int] = None
    koi_steff: Optional[float] = None
    koi_steff_err1: Optional[float] = None
    koi_steff_err2: Optional[float] = None
    koi_slogg: Optional[float] = None
    koi_slogg_err1: Optional[float] = None
    koi_slogg_err2: Optional[float] = None
    koi_srad: Optional[float] = None
    koi_srad_err1: Optional[float] = None
    koi_srad_err2: Optional[float] = None
    
    # Coordinates and magnitude
    ra: Optional[float] = None
    dec: Optional[float] = None
    koi_kepmag: Optional[float] = None
    
    # Disposition and scores
    koi_disposition: Optional[str] = None
    koi_pdisposition: Optional[str] = None
    koi_score: Optional[float] = None

class ExoplanetCandidateCreate(ExoplanetCandidateBase):
    pass

class ExoplanetCandidateUpdate(BaseModel):
    analysis_notes: Optional[str] = None
    final_verdict: Optional[FinalVerdict] = None
    quality_flags: Optional[str] = None

class ExoplanetCandidateResponse(ExoplanetCandidateBase):
    id: int
    researcher_id: int
    upload_timestamp: datetime
    analysis_status: AnalysisStatus
    final_verdict: FinalVerdict
    consensus_score: float
    ai_prediction: Optional[str] = None
    ai_confidence_score: Optional[float] = None
    discussion_thread_id: Optional[str] = None
    analysis_notes: Optional[str] = None
    quality_flags: Optional[str] = None
    
    class Config:
        orm_mode = True

class ExoplanetCandidateSummary(BaseModel):
    id: int
    kepid: Optional[int] = None
    kepoi_name: Optional[str] = None
    koi_period: Optional[float] = None
    koi_depth: Optional[float] = None
    analysis_status: AnalysisStatus
    final_verdict: FinalVerdict
    ai_prediction: Optional[str] = None
    ai_confidence_score: Optional[float] = None
    consensus_score: float
    upload_timestamp: datetime
    
    class Config:
        orm_mode = True

class PredictionRequest(BaseModel):
    candidate_id: int

class PredictionResponse(BaseModel):
    candidate_id: int
    prediction: str
    confidence_score: float
    analysis_timestamp: datetime

class CSVUploadResponse(BaseModel):
    message: str
    candidates_created: int
    upload_id: str
    filename: str
