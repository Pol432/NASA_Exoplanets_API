import secrets
from typing import Any, Dict, List, Optional, Union
from pydantic import validator, AnyHttpUrl
from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    # API Configuration
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    
    # Security
    ALLOWED_HOSTS: List[str] = ["*"]
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # Database Configuration
    DATABASE_URL: str = "postgresql://user:password@localhost/exoplanet_research"
    
    # File Upload Configuration
    UPLOAD_DIRECTORY: str = "uploads"
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_FILE_EXTENSIONS: List[str] = [".csv"]
    
    # ML Model Configuration
    ML_MODEL_PATH: str = "app/ml/saved_models/exoplanet_svm_model.pkl"
    SCALER_PATH: str = "app/ml/saved_models/scaler.pkl"
    ENABLE_MODEL_RETRAINING: bool = False
    
    # Organization Configuration
    ORGANIZATION_NAME: str = "Exoplanet Research Organization"
    ADMIN_EMAIL: str = "admin@exoplanet-research.org"
    
    # Feature Flags
    ENABLE_FORUM: bool = True
    REQUIRE_EMAIL_VERIFICATION: bool = False
    ENABLE_NOTIFICATIONS: bool = True
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    SESSION_TIMEOUT: int = 3600  # 1 hour
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
