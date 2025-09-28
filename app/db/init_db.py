from sqlalchemy.orm import Session
from app.db.base import engine, Base
from app.db.session import get_db  # Move import to top
from app.models.user import User
from app.models.exoplanet import ExoplanetCandidate
from app.models.analysis import AnalysisSession
from app.models.feedback import ResearcherFeedback
from app.services.user import UserService
from app.schemas.user import UserCreate
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

def init_db() -> None:
    """
    Initialize database tables and create default admin user
    """
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create default admin user if it doesn't exist
    db = next(get_db())
    try:
        admin_user = UserService.get_user_by_email(db, email=settings.ADMIN_EMAIL)
        if not admin_user:
            # Ensure the password is safe for bcrypt (max 72 bytes)
            admin_password = "admin123"  # Simple fallback
            
            # If using settings password, truncate it safely
            if hasattr(settings, 'ADMIN_PASSWORD') and settings.ADMIN_PASSWORD:
                admin_password = settings.ADMIN_PASSWORD
                # Truncate to ensure it's under 72 bytes
                if len(admin_password.encode('utf-8')) > 72:
                    admin_password = admin_password[:50]
                    logger.warning("Admin password was truncated for bcrypt compatibility")
            
            admin_user_data = UserCreate(
                username="admin",
                email=settings.ADMIN_EMAIL,
                password=admin_password,
                role="admin",
                research_specialization="exoplanet_detection"
            )
            
            logger.info(f"Creating admin user with email: {settings.ADMIN_EMAIL}")
            UserService.create_user(db=db, user=admin_user_data)
            logger.info(f"Created admin user: {settings.ADMIN_EMAIL}")
            
    except Exception as e:
        logger.error(f"Error creating admin user: {e}")
        raise
    finally:
        db.close()
