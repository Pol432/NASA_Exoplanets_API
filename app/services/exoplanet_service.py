from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from fastapi import HTTPException, status
from app.models.exoplanet import ExoplanetCandidate, AnalysisStatus, FinalVerdict
from app.schemas.exoplanet import ExoplanetCandidateCreate, ExoplanetCandidateUpdate
import pandas as pd
from datetime import datetime

class ExoplanetService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_candidate(self, candidate_data: ExoplanetCandidateCreate, user_id: int) -> ExoplanetCandidate:
        """Create a new exoplanet candidate"""
        db_candidate = ExoplanetCandidate(
            researcher_id=user_id,
            **candidate_data.dict()
        )
        
        self.db.add(db_candidate)
        self.db.commit()
        self.db.refresh(db_candidate)
        return db_candidate
    
    def get_candidate_by_id(self, candidate_id: int) -> Optional[ExoplanetCandidate]:
        """Get candidate by ID"""
        return self.db.query(ExoplanetCandidate).filter(
            ExoplanetCandidate.id == candidate_id
        ).first()
    
    def get_candidates(
        self, 
        skip: int = 0, 
        limit: int = 100,
        status_filter: Optional[AnalysisStatus] = None,
        verdict_filter: Optional[FinalVerdict] = None,
        user_id: Optional[int] = None
    ) -> List[ExoplanetCandidate]:
        """Get candidates with optional filters"""
        query = self.db.query(ExoplanetCandidate)
        
        if status_filter:
            query = query.filter(ExoplanetCandidate.analysis_status == status_filter)
        
        if verdict_filter:
            query = query.filter(ExoplanetCandidate.final_verdict == verdict_filter)
            
        if user_id:
            query = query.filter(ExoplanetCandidate.researcher_id == user_id)
        
        return query.offset(skip).limit(limit).all()
    
    def update_candidate(
        self, 
        candidate_id: int, 
        candidate_update: ExoplanetCandidateUpdate
    ) -> ExoplanetCandidate:
        """Update candidate information"""
        candidate = self.get_candidate_by_id(candidate_id)
        if not candidate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Candidate not found"
            )
        
        update_data = candidate_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(candidate, field, value)
        
        self.db.commit()
        self.db.refresh(candidate)
        return candidate
    
    def update_analysis_status(
        self, 
        candidate_id: int, 
        new_status: AnalysisStatus
    ) -> ExoplanetCandidate:
        """Update analysis status"""
        candidate = self.get_candidate_by_id(candidate_id)
        if not candidate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Candidate not found"
            )
        
        candidate.analysis_status = new_status
        self.db.commit()
        self.db.refresh(candidate)
        return candidate
    
    def update_ai_prediction(
        self, 
        candidate_id: int, 
        prediction: str, 
        confidence: float
    ) -> ExoplanetCandidate:
        """Update AI prediction results"""
        candidate = self.get_candidate_by_id(candidate_id)
        if not candidate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Candidate not found"
            )
        
        candidate.ai_prediction = prediction
        candidate.ai_confidence_score = confidence
        candidate.analysis_status = AnalysisStatus.COMPLETED
        
        self.db.commit()
        self.db.refresh(candidate)
        return candidate
    
    def bulk_create_from_csv(
        self, 
        df: pd.DataFrame, 
        filename: str, 
        user_id: int
    ) -> List[ExoplanetCandidate]:
        """Create multiple candidates from CSV data"""
        candidates = []
        
        for _, row in df.iterrows():
            # Convert row to dict and handle NaN values
            row_dict = row.to_dict()
            row_dict = {k: (v if pd.notna(v) else None) for k, v in row_dict.items()}
            
            candidate_data = ExoplanetCandidateCreate(
                original_csv_filename=filename,
                **row_dict
            )
            
            candidate = self.create_candidate(candidate_data, user_id)
            candidates.append(candidate)
        
        return candidates
    
    def get_candidates_needing_analysis(self) -> List[ExoplanetCandidate]:
        """Get candidates that need AI analysis"""
        return self.db.query(ExoplanetCandidate).filter(
            ExoplanetCandidate.analysis_status == AnalysisStatus.PENDING
        ).all()
    
    def calculate_consensus_score(self, candidate_id: int) -> float:
        """Calculate consensus score based on researcher feedback"""
        from app.models.feedback import ResearcherFeedback
        
        feedback_entries = self.db.query(ResearcherFeedback).filter(
            ResearcherFeedback.candidate_id == candidate_id
        ).all()
        
        if not feedback_entries:
            return 0.0
        
        # Weighted average of feedback scores
        total_weight = sum(fb.feedback_weight for fb in feedback_entries)
        weighted_score = sum(
            fb.confidence_score * fb.feedback_weight 
            for fb in feedback_entries
        )
        
        consensus_score = weighted_score / total_weight if total_weight > 0 else 0.0
        
        # Update candidate with new consensus score
        candidate = self.get_candidate_by_id(candidate_id)
        if candidate:
            candidate.consensus_score = consensus_score
            self.db.commit()
        
        return consensus_score
    
    def delete_candidate(self, candidate_id: int, user_id: int) -> None:
        """Delete candidate (only by owner or admin)"""
        candidate = self.get_candidate_by_id(candidate_id)
        if not candidate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Candidate not found"
            )
        
        # Check if user owns the candidate or is admin
        # This check would need to include role verification
        if candidate.researcher_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this candidate"
            )
        
        self.db.delete(candidate)
        self.db.commit()
