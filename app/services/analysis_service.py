from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.analysis import AnalysisSession
from app.schemas.analysis import AnalysisSessionCreate, AnalysisSessionUpdate

class AnalysisService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_session(self, session_data: AnalysisSessionCreate, user_id: int) -> AnalysisSession:
        """Create a new analysis session"""
        db_session = AnalysisSession(
            researcher_id=user_id,
            **session_data.dict()
        )
        
        self.db.add(db_session)
        self.db.commit()
        self.db.refresh(db_session)
        return db_session
    
    def get_session_by_id(self, session_id: int) -> Optional[AnalysisSession]:
        """Get analysis session by ID"""
        return self.db.query(AnalysisSession).filter(
            AnalysisSession.id == session_id
        ).first()
    
    def get_sessions_by_candidate(self, candidate_id: int) -> List[AnalysisSession]:
        """Get all sessions for a candidate"""
        return self.db.query(AnalysisSession).filter(
            AnalysisSession.candidate_id == candidate_id
        ).all()
    
    def get_sessions_by_researcher(self, researcher_id: int) -> List[AnalysisSession]:
        """Get all sessions by a researcher"""
        return self.db.query(AnalysisSession).filter(
            AnalysisSession.researcher_id == researcher_id
        ).all()
    
    def update_session(
        self, 
        session_id: int, 
        session_update: AnalysisSessionUpdate, 
        user_id: int
    ) -> AnalysisSession:
        """Update analysis session"""
        session = self.get_session_by_id(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis session not found"
            )
        
        # Check if user owns the session
        if session.researcher_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this session"
            )
        
        update_data = session_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(session, field, value)
        
        self.db.commit()
        self.db.refresh(session)
        return session
    
    def delete_session(self, session_id: int, user_id: int) -> None:
        """Delete analysis session"""
        session = self.get_session_by_id(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis session not found"
            )
        
        # Check if user owns the session or is admin
        if session.researcher_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this session"
            )
        
        self.db.delete(session)
        self.db.commit()
