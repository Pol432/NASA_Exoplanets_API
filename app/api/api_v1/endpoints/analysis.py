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
from app.models.exoplanet import AnalysisStatus, FinalVerdict, ExoplanetCandidate
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
    exoplanet_service.update_analysis_status(
        candidate_id, AnalysisStatus.PROCESSING)

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
        exoplanet_service.update_ai_prediction(
            candidate_id, prediction, confidence)

        logger.info(
            f"Completed ML prediction for candidate {candidate_id}: {prediction} ({confidence:.3f})")

    except Exception as e:
        logger.error(
            f"Error in ML prediction for candidate {candidate_id}: {e}")
        # Update status to error
        exoplanet_service.update_analysis_status(
            candidate_id, AnalysisStatus.ERROR)


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


@router.post("/bulk-predict")
def bulk_analyze_candidates(
    background_tasks: BackgroundTasks,
    filename: str = None,
    user_candidates_only: bool = True,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Run AI analysis on multiple candidates in bulk"""
    exoplanet_service = ExoplanetService(db)

    # Get candidates to analyze
    if filename:
        # Analyze candidates from a specific CSV file
        query = db.query(ExoplanetCandidate).filter(
            ExoplanetCandidate.original_csv_filename == filename
        )
        if user_candidates_only:
            query = query.filter(
                ExoplanetCandidate.researcher_id == current_user.id)
        candidates = query.all()
    else:
        # Analyze all pending candidates for the user
        candidates = exoplanet_service.get_candidates(
            limit=10000,  # Large limit to get all
            status_filter=AnalysisStatus.PENDING,
            user_id=current_user.id if user_candidates_only else None
        )

    if not candidates:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No candidates found for bulk analysis"
        )

    # Filter out already completed candidates
    pending_candidates = [
        c for c in candidates if c.analysis_status == AnalysisStatus.PENDING]

    if not pending_candidates:
        return {
            "message": "All candidates have already been analyzed",
            "total_candidates": len(candidates),
            "already_analyzed": len(candidates),
            "queued_for_analysis": 0
        }

    # Update all candidates to processing status
    candidate_ids = [c.id for c in pending_candidates]
    for candidate_id in candidate_ids:
        exoplanet_service.update_analysis_status(
            candidate_id, AnalysisStatus.PROCESSING)

    # Run bulk prediction in background
    background_tasks.add_task(run_bulk_ml_prediction, candidate_ids, db)

    return {
        "message": f"Bulk analysis started for {len(pending_candidates)} candidates",
        "total_candidates": len(candidates),
        "already_analyzed": len(candidates) - len(pending_candidates),
        "queued_for_analysis": len(pending_candidates),
        "candidate_ids": candidate_ids,
        "filename": filename
    }


def run_bulk_ml_prediction(candidate_ids: List[int], db: Session):
    """Background task to run ML prediction on multiple candidates"""
    try:
        exoplanet_service = ExoplanetService(db)
        ml_model = ExoplanetMLModel()

        logger.info(
            f"Starting bulk ML prediction for {len(candidate_ids)} candidates")

        # Process candidates in batches for better performance
        batch_size = 100
        total_processed = 0
        total_successful = 0
        total_errors = 0

        for i in range(0, len(candidate_ids), batch_size):
            batch_ids = candidate_ids[i:i + batch_size]

            # Get batch of candidates
            candidates = db.query(ExoplanetCandidate).filter(
                ExoplanetCandidate.id.in_(batch_ids)
            ).all()

            # Prepare batch data for prediction
            batch_data = []
            candidate_map = {}

            for candidate in candidates:
                candidate_data = {}
                for column in ml_model.feature_columns:
                    candidate_data[column] = getattr(candidate, column, None)
                batch_data.append(candidate_data)
                candidate_map[len(batch_data) - 1] = candidate.id

            if not batch_data:
                continue

            import pandas as pd
            df = pd.DataFrame(batch_data)

            try:
                # Make batch predictions
                predictions = ml_model.batch_predict(df)

                # Update candidates with results
                for idx, (prediction, confidence) in enumerate(predictions):
                    candidate_id = candidate_map[idx]
                    try:
                        exoplanet_service.update_ai_prediction(
                            candidate_id, prediction, confidence)
                        total_successful += 1
                        logger.info(
                            f"Completed prediction for candidate {candidate_id}: {prediction} ({confidence:.3f})")
                    except Exception as e:
                        logger.error(
                            f"Error updating candidate {candidate_id}: {e}")
                        exoplanet_service.update_analysis_status(
                            candidate_id, AnalysisStatus.ERROR)
                        total_errors += 1

            except Exception as e:
                logger.error(f"Error in batch prediction: {e}")
                # Mark all candidates in this batch as error
                for candidate_id in batch_ids:
                    exoplanet_service.update_analysis_status(
                        candidate_id, AnalysisStatus.ERROR)
                    total_errors += len(batch_ids)

            total_processed += len(batch_ids)
            logger.info(
                f"Processed batch {i//batch_size + 1}: {total_processed}/{len(candidate_ids)} candidates")

        logger.info(
            f"Bulk ML prediction completed: {total_successful} successful, {total_errors} errors out of {len(candidate_ids)} total")

    except Exception as e:
        logger.error(f"Error in bulk ML prediction: {e}")
        # Mark remaining candidates as error
        for candidate_id in candidate_ids:
            try:
                exoplanet_service.update_analysis_status(
                    candidate_id, AnalysisStatus.ERROR)
            except:
                pass


@router.get("/bulk-status")
def get_bulk_analysis_status(
    filename: str = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get status of bulk analysis"""
    exoplanet_service = ExoplanetService(db)

    # Build query
    query = db.query(ExoplanetCandidate).filter(
        ExoplanetCandidate.researcher_id == current_user.id
    )

    if filename:
        query = query.filter(
            ExoplanetCandidate.original_csv_filename == filename)

    candidates = query.all()

    if not candidates:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No candidates found"
        )

    # Count by status
    status_counts = {}
    for candidate in candidates:
        status = candidate.analysis_status.value
        status_counts[status] = status_counts.get(status, 0) + 1

    # Count by prediction
    prediction_counts = {}
    for candidate in candidates:
        if candidate.ai_prediction:
            pred = candidate.ai_prediction
            prediction_counts[pred] = prediction_counts.get(pred, 0) + 1

    return {
        "total_candidates": len(candidates),
        "status_breakdown": status_counts,
        "prediction_breakdown": prediction_counts,
        "filename": filename,
        "completed_percentage": round((status_counts.get("completed", 0) / len(candidates)) * 100, 2)
    }
