from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.services.auth import get_current_active_user
from app.services.feedback_service import FeedbackService
from app.models.user import User
from app.schemas.feedback import (
    ResearcherFeedbackCreate, ResearcherFeedbackUpdate, ResearcherFeedbackResponse,
    FeedbackConsensus, ResearcherStats
)

router = APIRouter()

@router.post("/submit", response_model=ResearcherFeedbackResponse, status_code=status.HTTP_201_CREATED)
def submit_feedback(
    feedback_data: ResearcherFeedbackCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Submit researcher feedback for an exoplanet candidate"""
    feedback_service = FeedbackService(db)
    return feedback_service.create_feedback(feedback_data, current_user.id)

@router.get("/candidate/{candidate_id}", response_model=List[ResearcherFeedbackResponse])
def get_candidate_feedback(
    candidate_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all feedback for a specific candidate"""
    feedback_service = FeedbackService(db)
    return feedback_service.get_feedback_by_candidate(candidate_id)

@router.get("/my-feedback", response_model=List[ResearcherFeedbackResponse])
def get_my_feedback(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current user's feedback entries"""
    feedback_service = FeedbackService(db)
    return feedback_service.get_feedback_by_researcher(current_user.id, skip, limit)

@router.put("/{feedback_id}", response_model=ResearcherFeedbackResponse)
def update_feedback(
    feedback_id: int,
    feedback_update: ResearcherFeedbackUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update existing feedback entry"""
    feedback_service = FeedbackService(db)
    return feedback_service.update_feedback(feedback_id, feedback_update, current_user.id)

@router.delete("/{feedback_id}", status_code=status.HTTP_200_OK)
def delete_feedback(
    feedback_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete feedback entry"""
    feedback_service = FeedbackService(db)
    feedback_service.delete_feedback(feedback_id, current_user.id)
    return {"message": "Feedback deleted successfully"}

@router.get("/consensus/{candidate_id}", response_model=FeedbackConsensus)
def get_consensus_score(
    candidate_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Calculate and return consensus score for a candidate"""
    feedback_service = FeedbackService(db)
    consensus_data = feedback_service.calculate_consensus_score(candidate_id)
    return FeedbackConsensus(candidate_id=candidate_id, **consensus_data)

@router.get("/researcher/{researcher_id}/stats", response_model=ResearcherStats)
def get_researcher_stats(
    researcher_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get statistics for a researcher's feedback history"""
    feedback_service = FeedbackService(db)
    stats_data = feedback_service.get_researcher_statistics(researcher_id)
    return ResearcherStats(researcher_id=researcher_id, **stats_data)

@router.get("/my-stats", response_model=ResearcherStats)
def get_my_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current user's feedback statistics"""
    feedback_service = FeedbackService(db)
    stats_data = feedback_service.get_researcher_statistics(current_user.id)
    return ResearcherStats(researcher_id=current_user.id, **stats_data)

@router.get("/{feedback_id}", response_model=ResearcherFeedbackResponse)
def get_feedback_by_id(
    feedback_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get specific feedback entry by ID"""
    feedback_service = FeedbackService(db)
    feedback = feedback_service.get_feedback_by_id(feedback_id)
    
    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found"
        )
    
    return feedback
