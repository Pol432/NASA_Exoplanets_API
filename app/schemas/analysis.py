from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime

class AnalysisSessionBase(BaseModel):
    candidate_id: int
    methodology_used: Optional[str] = None
    analysis_notes: Optional[str] = None
    key_observations: Optional[str] = None
    concerns_raised: Optional[str] = None

class AnalysisSessionCreate(AnalysisSessionBase):
    pass

class AnalysisSessionUpdate(BaseModel):
    researcher_verdict: Optional[str] = None
    confidence_level: Optional[float] = None
    methodology_used: Optional[str] = None
    analysis_notes: Optional[str] = None
    key_observations: Optional[str] = None
    concerns_raised: Optional[str] = None
    time_spent_analyzing: Optional[int] = None
    session_completed: Optional[bool] = None
    
    @validator('confidence_level')
    def validate_confidence(cls, v):
        if v is not None and (v < 0.0 or v > 1.0):
            raise ValueError('Confidence level must be between 0.0 and 1.0')
        return v

class AnalysisSessionResponse(AnalysisSessionBase):
    id: int
    researcher_id: int
    session_timestamp: datetime
    researcher_verdict: Optional[str] = None
    confidence_level: Optional[float] = None
    time_spent_analyzing: int
    session_completed: bool
    
    class Config:
        orm_mode = True
