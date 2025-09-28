from fastapi import APIRouter
from app.api.api_v1.endpoints import auth, data_upload, analysis, feedback

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(data_upload.router, prefix="/data", tags=["data-upload"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["analysis"])
api_router.include_router(feedback.router, prefix="/feedback", tags=["feedback"])

