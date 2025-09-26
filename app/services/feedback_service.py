from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.feedback import ResearcherFeedback
from app.models.user import User, UserRole
from app.schemas.feedback import ResearcherFeedbackCreate, ResearcherFeedbackUpdate
from sqlalchemy import func

class FeedbackService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_feedback(self, feedback_data: ResearcherFeedbackCreate, user_id: int) -> ResearcherFeedback:
        """Create new researcher feedback"""
        # Check if user already provided feedback for this candidate
        existing_feedback = self.db.query(ResearcherFeedback).filter(
            ResearcherFeedback.candidate_id == feedback_data.candidate_id,
            ResearcherFeedback.researcher_id == user_id
        ).first()
        
        if existing_feedback:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You have already provided feedback for this candidate"
            )
        
        # Calculate feedback weight based on user experience/role
        feedback_weight = self._calculate_feedback_weight(user_id)
        
        db_feedback = ResearcherFeedback(
            researcher_id=user_id,
            feedback_weight=feedback_weight,
            **feedback_data.dict()
        )
        
        self.db.add(db_feedback)
        self.db.commit()
        self.db.refresh(db_feedback)
        return db_feedback
    
    def get_feedback_by_id(self, feedback_id: int) -> Optional[ResearcherFeedback]:
        """Get feedback by ID"""
        return self.db.query(ResearcherFeedback).filter(
            ResearcherFeedback.id == feedback_id
        ).first()
    
    def get_feedback_by_candidate(self, candidate_id: int) -> List[ResearcherFeedback]:
        """Get all feedback for a specific candidate"""
        return self.db.query(ResearcherFeedback).filter(
            ResearcherFeedback.candidate_id == candidate_id
        ).order_by(ResearcherFeedback.feedback_timestamp.desc()).all()
    
    def get_feedback_by_researcher(self, researcher_id: int, skip: int = 0, limit: int = 100) -> List[ResearcherFeedback]:
        """Get all feedback by a specific researcher"""
        return self.db.query(ResearcherFeedback).filter(
            ResearcherFeedback.researcher_id == researcher_id
        ).offset(skip).limit(limit).all()
    
    def update_feedback(
        self, 
        feedback_id: int, 
        feedback_update: ResearcherFeedbackUpdate, 
        user_id: int
    ) -> ResearcherFeedback:
        """Update existing feedback"""
        feedback = self.get_feedback_by_id(feedback_id)
        if not feedback:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Feedback not found"
            )
        
        # Check if user owns the feedback
        if feedback.researcher_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this feedback"
            )
        
        update_data = feedback_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(feedback, field, value)
        
        self.db.commit()
        self.db.refresh(feedback)
        return feedback
    
    def delete_feedback(self, feedback_id: int, user_id: int) -> None:
        """Delete feedback"""
        feedback = self.get_feedback_by_id(feedback_id)
        if not feedback:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Feedback not found"
            )
        
        # Check if user owns the feedback or is admin
        if feedback.researcher_id != user_id:
            # TODO: Add admin role check here
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this feedback"
            )
        
        self.db.delete(feedback)
        self.db.commit()
    
    def calculate_consensus_score(self, candidate_id: int) -> Dict:
        """Calculate detailed consensus statistics for a candidate"""
        feedback_entries = self.get_feedback_by_candidate(candidate_id)
        
        if not feedback_entries:
            return {
                "consensus_score": 0.0,
                "total_feedback": 0,
                "agreement_rate": 0.0,
                "classification_breakdown": {},
                "average_confidence": 0.0
            }
        
        total_weight = sum(fb.feedback_weight for fb in feedback_entries)
        weighted_confidence = sum(
            fb.confidence_score * fb.feedback_weight 
            for fb in feedback_entries
        )
        
        # Calculate classification breakdown
        classification_counts = {}
        for fb in feedback_entries:
            classification = fb.expert_classification
            if classification not in classification_counts:
                classification_counts[classification] = 0
            classification_counts[classification] += 1
        
        # Calculate agreement with AI
        ai_agreement_count = sum(1 for fb in feedback_entries if fb.agrees_with_ai)
        agreement_rate = ai_agreement_count / len(feedback_entries)
        
        consensus_score = weighted_confidence / total_weight if total_weight > 0 else 0.0
        average_confidence = sum(fb.confidence_score for fb in feedback_entries) / len(feedback_entries)
        
        return {
            "consensus_score": consensus_score,
            "total_feedback": len(feedback_entries),
            "agreement_rate": agreement_rate,
            "classification_breakdown": classification_counts,
            "average_confidence": average_confidence,
            "weighted_total": total_weight
        }
    
    def _calculate_feedback_weight(self, user_id: int) -> float:
        """Calculate feedback weight based on user experience and role"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return 1.0
        
        base_weight = 1.0
        
        # Role-based weight adjustment
        role_weights = {
            UserRole.RESEARCHER: 1.0,
            UserRole.MODERATOR: 1.2,
            UserRole.ADMIN: 1.5
        }
        
        base_weight = role_weights.get(user.role, 1.0)
        
        # Experience-based adjustment (based on number of previous feedback)
        previous_feedback_count = self.db.query(func.count(ResearcherFeedback.id)).filter(
            ResearcherFeedback.researcher_id == user_id
        ).scalar()
        
        # Gradually increase weight based on experience (max 2.0x multiplier)
        experience_multiplier = min(1.0 + (previous_feedback_count * 0.01), 2.0)
        
        return base_weight * experience_multiplier
    
    def get_researcher_statistics(self, researcher_id: int) -> Dict:
        """Get statistics for a researcher's feedback history"""
        feedback_list = self.get_feedback_by_researcher(researcher_id, limit=1000)
        
        if not feedback_list:
            return {
                "total_feedback": 0,
                "average_confidence": 0.0,
                "classification_breakdown": {},
                "ai_agreement_rate": 0.0
            }
        
        total_feedback = len(feedback_list)
        average_confidence = sum(fb.confidence_score for fb in feedback_list) / total_feedback
        
        # Classification breakdown
        classification_counts = {}
        ai_agreements = 0
        
        for fb in feedback_list:
            classification = fb.expert_classification
            if classification not in classification_counts:
                classification_counts[classification] = 0
            classification_counts[classification] += 1
            
            if fb.agrees_with_ai:
                ai_agreements += 1
        
        ai_agreement_rate = ai_agreements / total_feedback
        
        return {
            "total_feedback": total_feedback,
            "average_confidence": average_confidence,
            "classification_breakdown": classification_counts,
            "ai_agreement_rate": ai_agreement_rate
        }
