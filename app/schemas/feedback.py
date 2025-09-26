from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime

class ResearcherFeedbackBase(BaseModel):
    candidate_id: int
    expert_classification: str
    detailed_reasoning: str
    confidence_score: float
    agrees_with_ai: Optional[bool] = None
    supporting_data_references: Optional[str] = None
    methodology_description: Optional[str] = None
    time_spent_on_analysis: Optional[int] = None  # minutes
    tools_used: Optional[str] = None
    
    @validator('confidence_score')
    def validate_confidence_score(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Confidence score must be between 0.0 and 1.0')
        return v
    
    @validator('expert_classification')
    def validate_classification(cls, v):
        valid_classifications = ["CONFIRMED", "FALSE_POSITIVE", "CANDIDATE"]
        if v not in valid_classifications:
            raise ValueError(f'Classification must be one of: {valid_classifications}')
        return v
    
    @validator('time_spent_on_analysis')
    def validate_time_spent(cls, v):
        if v is not None and v < 0:
            raise ValueError('Time spent must be non-negative')
        return v

class ResearcherFeedbackCreate(ResearcherFeedbackBase):
    pass

class ResearcherFeedbackUpdate(BaseModel):
    expert_classification: Optional[str] = None
    detailed_reasoning: Optional[str] = None
    confidence_score: Optional[float] = None
    agrees_with_ai: Optional[bool] = None
    supporting_data_references: Optional[str] = None
    methodology_description: Optional[str] = None
    time_spent_on_analysis: Optional[int] = None
    tools_used: Optional[str] = None
    
    @validator('confidence_score')
    def validate_confidence_score(cls, v):
        if v is not None and not 0.0 <= v <= 1.0:
            raise ValueError('Confidence score must be between 0.0 and 1.0')
        return v
    
    @validator('expert_classification')
    def validate_classification(cls, v):
        if v is not None:
            valid_classifications = ["CONFIRMED", "FALSE_POSITIVE", "CANDIDATE"]
            if v not in valid_classifications:
                raise ValueError(f'Classification must be one of: {valid_classifications}')
        return v

class ResearcherFeedbackResponse(ResearcherFeedbackBase):
    id: int
    researcher_id: int
    feedback_timestamp: datetime
    feedback_weight: float
    peer_review_status: str
    
    class Config:
        orm_mode = True

class FeedbackConsensus(BaseModel):
    candidate_id: int
    consensus_score: float
    total_feedback: int
    agreement_rate: float
    classification_breakdown: dict
    average_confidence: float
    weighted_total: float

class ResearcherStats(BaseModel):
    researcher_id: int
    total_feedback: int
    average_confidence: float
    classification_breakdown: dict
    ai_agreement_rate: float
