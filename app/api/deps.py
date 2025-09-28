from typing import Generator
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from auth_shared.jwt import JWTAuth
from app.db.session import get_db
from app.services.user import UserService
from app.services.exoplanet_service import ExoplanetService
from app.services.analysis_service import AnalysisService
from app.services.feedback_service import FeedbackService

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> int:
    token = credentials.credentials

    try:
        payload = JWTAuth.verify_token(token)
        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )
        return user_id

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

def get_database() -> Generator[Session, None, None]:
    """Database dependency for FastAPI endpoints"""
    try:
        db = next(get_db())
        yield db
    finally:
        db.close()

def get_exoplanet_service(db: Session = Depends(get_db)) -> ExoplanetService:
    """Get exoplanet service instance"""
    return ExoplanetService(db)

def get_analysis_service(db: Session = Depends(get_db)) -> AnalysisService:
    """Get analysis service instance"""
    return AnalysisService(db)

def get_feedback_service(db: Session = Depends(get_db)) -> FeedbackService:
    """Get feedback service instance"""
    return FeedbackService(db)

def get_ml_model():
    """Get ML model instance"""
    from app.ml.model_handler import get_ml_model
    return get_ml_model()
