from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.services.auth import get_current_active_user
from app.services.exoplanet_service import ExoplanetService
from app.services.analysis_service import AnalysisService
from app.models.user import User
from app.schemas.exoplanet import PredictionRequest, PredictionResponse, ExoplanetCandidateResponse
from app.schemas.analysis import AnalysisSessionCreate, AnalysisSessionResponse, AnalysisSessionUpdate
from app.ml.model_handler import ExoplanetMLModel
from app.models.exoplanet import AnalysisStatus, FinalVerdict
from datetime import datetime
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/predict/{candidate_id}", response_model=PredictionResponse)
def analyze_candidate(
    candidate_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Run AI analysis on an exoplanet candidate"""
    exoplanet_service = ExoplanetService(db)
    
    # Get the candidate
    candidate = exoplanet_service.get_candidate_by_id(candidate_id)
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found"
        )
    
    # Check if already analyzed
    if candidate.analysis_status == AnalysisStatus.COMPLETED:
        return PredictionResponse(
            candidate_id=candidate_id,
            prediction=candidate.ai_prediction,
            confidence_score=candidate.ai_confidence_score,
            analysis_timestamp=candidate.upload_timestamp
        )
    
    # Update status to processing
    exoplanet_service.update_analysis_status(candidate_id, AnalysisStatus.PROCESSING)
    
    # Run prediction in background
    background_tasks.add_task(run_ml_prediction, candidate_id, db)
    
    return PredictionResponse(
        candidate_id=candidate_id,
        prediction="PROCESSING",
        confidence_score=0.0,
        analysis_timestamp=datetime.utcnow()
    )

def run_ml_prediction(candidate_id: int, db: Session):
    """Background task to run ML prediction"""
    try:
        exoplanet_service = ExoplanetService(db)
        candidate = exoplanet_service.get_candidate_by_id(candidate_id)
        
        if not candidate:
            logger.error(f"Candidate {candidate_id} not found for prediction")
            return
        
        # Initialize ML model
        ml_model = ExoplanetMLModel()
        
        # Prepare data for prediction
        import pandas as pd
        
        # Create DataFrame from candidate data
        candidate_data = {}
        for column in ml_model.feature_columns:
            candidate_data[column] = [getattr(candidate, column, None)]
        
        df = pd.DataFrame(candidate_data)
        
        # Make prediction
        prediction, confidence = ml_model.predict(ml_model.preprocess_data(df))
        
        # Update candidate with results
        exoplanet_service.update_ai_prediction(candidate_id, prediction, confidence)
        
        logger.info(f"Completed ML prediction for candidate {candidate_id}: {prediction} ({confidence:.3f})")
        
    except Exception as e:
        logger.error(f"Error in ML prediction for candidate {candidate_id}: {e}")
        # Update status to error
        exoplanet_service.update_analysis_status(candidate_id, AnalysisStatus.ERROR)

@router.get("/results/{candidate_id}", response_model=ExoplanetCandidateResponse)
def get_analysis_results(
    candidate_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get analysis results for a candidate"""
    exoplanet_service = ExoplanetService(db)
    candidate = exoplanet_service.get_candidate_by_id(candidate_id)
    
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found"
        )
    
    return candidate

@router.put("/results/{candidate_id}/verdict")
def update_researcher_verdict(
    candidate_id: int,
    verdict: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update researcher's verdict on a candidate"""
    try:
        verdict_enum = FinalVerdict(verdict)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid verdict: {verdict}"
        )
    
    exoplanet_service = ExoplanetService(db)
    candidate = exoplanet_service.get_candidate_by_id(candidate_id)
    
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found"
        )
    
    # Update the verdict
    candidate.final_verdict = verdict_enum
    db.commit()
    
    # Recalculate consensus score
    consensus_score = exoplanet_service.calculate_consensus_score(candidate_id)
    
    return {
        "message": "Verdict updated successfully",
        "new_verdict": verdict,
        "consensus_score": consensus_score
    }

@router.post("/sessions", response_model=AnalysisSessionResponse, status_code=status.HTTP_201_CREATED)
def create_analysis_session(
    session_data: AnalysisSessionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new analysis session"""
    analysis_service = AnalysisService(db)
    return analysis_service.create_session(session_data, current_user.id)

@router.get("/sessions/{session_id}", response_model=AnalysisSessionResponse)
def get_analysis_session(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get analysis session details"""
    analysis_service = AnalysisService(db)
    session = analysis_service.get_session_by_id(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis session not found"
        )
    
    return session

@router.put("/sessions/{session_id}", response_model=AnalysisSessionResponse)
def update_analysis_session(
    session_id: int,
    session_update: AnalysisSessionUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update analysis session"""
    analysis_service = AnalysisService(db)
    return analysis_service.update_session(session_id, session_update, current_user.id)

@router.get("/sessions/candidate/{candidate_id}", response_model=List[AnalysisSessionResponse])
def get_candidate_sessions(
    candidate_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all analysis sessions for a candidate"""
    analysis_service = AnalysisService(db)
    return analysis_service.get_sessions_by_candidate(candidate_id)

@router.get("/candidates/pending", response_model=List[ExoplanetCandidateResponse])
def get_pending_candidates(
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get candidates that need analysis"""
    exoplanet_service = ExoplanetService(db)
    return exoplanet_service.get_candidates(
        limit=limit,
        status_filter=AnalysisStatus.PENDING
    )
