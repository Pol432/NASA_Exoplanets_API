from typing import Generator
from sqlalchemy.orm import Session
from app.db.base import SessionLocal

def get_db() -> Generator[Session, None, None]:
    """
    Database dependency for FastAPI endpoints
    """
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()
