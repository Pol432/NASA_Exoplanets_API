import joblib
import numpy as np
import pandas as pd
from typing import Tuple, List, Optional
from sklearn.preprocessing import StandardScaler
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class ExoplanetMLModel:
    def __init__(self):
        self.model = None
        self.scaler = None
        self.feature_columns = [
            'koi_period', 'koi_time0bk', 'koi_impact', 'koi_duration', 'koi_depth',
            'koi_prad', 'koi_teq', 'koi_insol', 'koi_model_snr', 'koi_tce_plnt_num',
            'koi_steff', 'koi_slogg', 'koi_srad', 'ra', 'dec', 'koi_kepmag',
            'koi_period_err1', 'koi_period_err2', 'koi_time0bk_err1', 'koi_time0bk_err2',
            'koi_impact_err1', 'koi_impact_err2', 'koi_duration_err1', 'koi_duration_err2',
            'koi_depth_err1', 'koi_depth_err2', 'koi_prad_err1', 'koi_prad_err2',
            'koi_teq_err1', 'koi_teq_err2', 'koi_insol_err1', 'koi_insol_err2',
            'koi_steff_err1', 'koi_steff_err2', 'koi_slogg_err1', 'koi_slogg_err2',
            'koi_srad_err1', 'koi_srad_err2', 'koi_score'
        ]
        self.load_model()
    
    def load_model(self) -> None:
        """Load the trained ML model and scaler"""
        try:
            self.model = joblib.load(settings.ML_MODEL_PATH)
            self.scaler = joblib.load(settings.SCALER_PATH)
            logger.info("ML model and scaler loaded successfully")
        except Exception as e:
            logger.error(f"Error loading ML model: {e}")
            self.model = None
            self.scaler = None
    
    def preprocess_data(self, df: pd.DataFrame) -> np.ndarray:
        """Preprocess data for model prediction"""
        try:
            # Select only the features used in training
            feature_df = df[self.feature_columns].copy()
            
            # Handle missing values (use median for numerical features)
            feature_df = feature_df.fillna(feature_df.median())
            
            # Scale the features
            if self.scaler is not None:
                scaled_features = self.scaler.transform(feature_df)
            else:
                scaled_features = feature_df.values
                
            return scaled_features
            
        except Exception as e:
            logger.error(f"Error preprocessing data: {e}")
            raise ValueError(f"Data preprocessing failed: {e}")
    
    def predict(self, features: np.ndarray) -> Tuple[str, float]:
        """Make prediction on preprocessed features"""
        if self.model is None:
            raise ValueError("Model not loaded")
        
        try:
            # Get prediction and confidence
            prediction = self.model.predict(features)
            
            # Get prediction probabilities if available
            if hasattr(self.model, 'predict_proba'):
                probabilities = self.model.predict_proba(features)
                confidence = np.max(probabilities, axis=1)[0]
            elif hasattr(self.model, 'decision_function'):
                # For SVM
                decision_scores = self.model.decision_function(features)
                # Convert decision scores to confidence (0-1 range)
                confidence = 1 / (1 + np.exp(-abs(decision_scores[0])))
            else:
                confidence = 0.8  # Default confidence if unavailable
            
            # Map prediction to string
            prediction_map = {
                0: "FALSE POSITIVE",
                1: "CONFIRMED", 
                2: "CANDIDATE"
            }
            
            prediction_str = prediction_map.get(prediction[0], "UNKNOWN")
            
            return prediction_str, float(confidence)
            
        except Exception as e:
            logger.error(f"Error making prediction: {e}")
            raise ValueError(f"Prediction failed: {e}")
    
    def validate_input_format(self, df: pd.DataFrame) -> bool:
        """Validate that input DataFrame has required columns"""
        missing_columns = set(self.feature_columns) - set(df.columns)
        if missing_columns:
            logger.warning(f"Missing columns: {missing_columns}")
            return False
        return True
    
    def batch_predict(self, df: pd.DataFrame) -> List[Tuple[str, float]]:
        """Make predictions for multiple samples"""
        try:
            if not self.validate_input_format(df):
                raise ValueError("Invalid input format")
            
            features = self.preprocess_data(df)
            predictions = []
            
            for i in range(len(features)):
                pred, conf = self.predict(features[i:i+1])
                predictions.append((pred, conf))
            
            return predictions
            
        except Exception as e:
            logger.error(f"Error in batch prediction: {e}")
            raise
    
    def retrain_with_feedback(self, training_data: pd.DataFrame) -> None:
        """Retrain model with new feedback data (placeholder)"""
        # This would implement model retraining logic
        # For now, just log the request
        logger.info(f"Model retraining requested with {len(training_data)} samples")
        # TODO: Implement actual retraining logic

# Global instance for dependency injection
_ml_model_instance = None

def get_ml_model() -> ExoplanetMLModel:
    """Get ML model instance (singleton pattern)"""
    global _ml_model_instance
    if _ml_model_instance is None:
        _ml_model_instance = ExoplanetMLModel()
    return _ml_model_instance
