from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.session import get_db
from app.services.auth import get_current_active_user
from app.services.exoplanet_service import ExoplanetService
from app.models.user import User
from app.schemas.exoplanet import ExoplanetCandidateResponse, CSVUploadResponse, ExoplanetCandidateSummary
from app.utils.csv_processor import CSVProcessor
from app.core.config import settings
import uuid
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/upload-csv", response_model=CSVUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_csv(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Upload astronomical data CSV file"""
    
    # Validate file type
    if not file.filename.lower().endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are allowed"
        )
    
    # Read content
    content = await file.read()

    # Check file size
    if len(content) > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum allowed size of {settings.MAX_FILE_SIZE} bytes"
        )
    
    try:
        # Process CSV content
        df, validation_result = CSVProcessor.process_csv_content(content, file.filename)
        
        logger.info(f"Processing CSV upload from user {current_user.id}: {file.filename}")
        
        # Create exoplanet service instance
        exoplanet_service = ExoplanetService(db)
        
        # Create candidates from CSV data
        candidates = exoplanet_service.bulk_create_from_csv(
            df=df,
            filename=file.filename,
            user_id=current_user.id
        )
        
        upload_id = str(uuid.uuid4())
        
        return CSVUploadResponse(
            message=f"Successfully uploaded {len(candidates)} exoplanet candidates",
            candidates_created=len(candidates),
            upload_id=upload_id,
            filename=file.filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing CSV upload: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing CSV file"
        )


@router.get("/uploads/me", response_model=List[ExoplanetCandidateSummary])
def get_my_uploads(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current user's uploaded candidates"""
    exoplanet_service = ExoplanetService(db)
    candidates = exoplanet_service.get_candidates(
        skip=skip,
        limit=limit,
        user_id=current_user.id
    )
    return candidates


@router.get("/uploads/{candidate_id}", response_model=ExoplanetCandidateResponse)
def get_upload_details(
    candidate_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific candidate"""
    exoplanet_service = ExoplanetService(db)
    candidate = exoplanet_service.get_candidate_by_id(candidate_id)
    
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found"
        )
    
    return candidate


@router.delete("/uploads/{candidate_id}", status_code=status.HTTP_200_OK)
def delete_upload(
    candidate_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete an uploaded candidate"""
    exoplanet_service = ExoplanetService(db)
    exoplanet_service.delete_candidate(candidate_id, current_user.id)
    return {"message": "Candidate deleted successfully"}


@router.get("/candidates", response_model=List[ExoplanetCandidateSummary])
def list_all_candidates(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = None,
    verdict_filter: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all candidates with optional filters"""
    from app.models.exoplanet import AnalysisStatus, FinalVerdict
    
    # Convert string filters to enums
    status_enum = None
    if status_filter:
        try:
            status_enum = AnalysisStatus(status_filter)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status filter: {status_filter}"
            )
    
    verdict_enum = None
    if verdict_filter:
        try:
            verdict_enum = FinalVerdict(verdict_filter)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid verdict filter: {verdict_filter}"
            )
    
    exoplanet_service = ExoplanetService(db)
    candidates = exoplanet_service.get_candidates(
        skip=skip,
        limit=limit,
        status_filter=status_enum,
        verdict_filter=verdict_enum
    )
    
    return candidates