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
        # Updated feature columns to match the actual trained model (21 features)
        self.feature_columns = [
            'koi_score',
            'koi_fpflag_nt',
            'koi_fpflag_ss',
            'koi_fpflag_co',
            'koi_fpflag_ec',
            'koi_period',
            'koi_time0bk',
            'koi_impact',
            'koi_duration',
            'koi_depth',
            'koi_prad',
            'koi_teq',
            'koi_insol',
            'koi_model_snr',
            'koi_tce_plnt_num',
            'koi_steff',
            'koi_slogg',
            'koi_srad',
            'ra',
            'dec',
            'koi_kepmag'
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

    def preprocess_data(self, df: pd.DataFrame):
        """Preprocess data for model prediction"""
        try:
            # Create a copy of the dataframe
            feature_df = df.copy()

            # Add missing flag columns with default values if they don't exist
            flag_columns = ['koi_fpflag_ss', 'koi_fpflag_co',
                            'koi_fpflag_nt', 'koi_fpflag_ec']
            for col in flag_columns:
                if col not in feature_df.columns:
                    feature_df[col] = 0  # Default flag value

            # Select only the features used in training
            feature_df = feature_df[self.feature_columns].copy()

            # Handle missing values
            # For flag columns, fill with 0
            for col in flag_columns:
                if col in feature_df.columns:
                    feature_df[col] = feature_df[col].fillna(0)

            # For numerical features, use median (but handle cases where all values are NaN)
            numerical_cols = [
                col for col in self.feature_columns if col not in flag_columns]
            for col in numerical_cols:
                if col in feature_df.columns:
                    if not feature_df[col].isna().all():
                        feature_df[col] = feature_df[col].fillna(
                            feature_df[col].median())
                    else:
                        # If all values are NaN, fill with a default value
                        default_values = {
                            'koi_period': 10.0,
                            'koi_time0bk': 131.0,
                            'koi_impact': 0.5,
                            'koi_duration': 3.0,
                            'koi_depth': 100.0,
                            'koi_prad': 2.0,
                            'koi_teq': 1000.0,
                            'koi_insol': 1000.0,
                            'koi_model_snr': 10.0,
                            'koi_tce_plnt_num': 1,
                            'koi_steff': 5000.0,
                            'koi_slogg': 4.0,
                            'koi_srad': 1.0,
                            'ra': 180.0,
                            'dec': 0.0,
                            'koi_kepmag': 14.0,
                            'koi_score': 0.5
                        }
                        feature_df[col] = feature_df[col].fillna(
                            default_values.get(col, 0.0))

            # Scale the features
            if self.scaler is not None:
                scaled_features = self.scaler.transform(feature_df)
                # Convert back to DataFrame to preserve feature names
                scaled_df = pd.DataFrame(
                    scaled_features, columns=self.feature_columns)
                return scaled_df
            else:
                return feature_df

        except Exception as e:
            logger.error(f"Error preprocessing data: {e}")
            raise ValueError(f"Data preprocessing failed: {e}")

    def predict(self, features) -> Tuple[str, float]:
        """Make prediction on preprocessed features"""
        if self.model is None:
            raise ValueError("Model not loaded")

        try:
            # Get prediction and confidence
            prediction = self.model.predict(features)

            # Log the actual prediction value for debugging
            logger.info(f"Raw model prediction: {prediction}")
            logger.info(f"Prediction type: {type(prediction)}")
            logger.info(
                f"Prediction shape: {prediction.shape if hasattr(prediction, 'shape') else 'No shape'}")

            # Get prediction probabilities if available
            if hasattr(self.model, 'predict_proba'):
                probabilities = self.model.predict_proba(features)
                confidence = np.max(probabilities, axis=1)[0]
                logger.info(f"Prediction probabilities: {probabilities}")
            elif hasattr(self.model, 'decision_function'):
                # For SVM
                decision_scores = self.model.decision_function(features)
                # Convert decision scores to confidence (0-1 range)
                confidence = 1 / (1 + np.exp(-abs(decision_scores[0])))
                logger.info(f"Decision scores: {decision_scores}")
            else:
                confidence = 0.8  # Default confidence if unavailable

            # Map prediction to string - handle different possible prediction formats
            pred_value = prediction[0] if hasattr(
                prediction, '__len__') else prediction

            # Try different mapping approaches
            prediction_map = {
                0: "FALSE POSITIVE",
                1: "CONFIRMED",
                2: "CANDIDATE",
                "FALSE POSITIVE": "FALSE POSITIVE",
                "CONFIRMED": "CONFIRMED",
                "CANDIDATE": "CANDIDATE"
            }

            prediction_str = prediction_map.get(
                pred_value, f"UNKNOWN({pred_value})")

            logger.info(
                f"Final prediction: {prediction_str} (confidence: {confidence})")

            return prediction_str, float(confidence)

        except Exception as e:
            logger.error(f"Error making prediction: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise ValueError(f"Prediction failed: {e}")

    def validate_input_format(self, df: pd.DataFrame) -> bool:
        """Validate that input DataFrame has required columns"""
        missing_columns = set(self.feature_columns) - set(df.columns)
        if missing_columns:
            logger.warning(f"Missing columns: {missing_columns}")
            # Allow missing flag columns and some other columns as they can be filled with defaults
            flag_columns = ['koi_fpflag_ss', 'koi_fpflag_co',
                            'koi_fpflag_nt', 'koi_fpflag_ec']
            # Also allow some other columns to be missing as they can be filled with defaults
            optional_columns = flag_columns + ['koi_impact', 'koi_duration', 'koi_depth',
                                               'koi_prad', 'koi_insol', 'koi_steff', 'koi_slogg', 'koi_srad', 'dec']
            critical_missing = missing_columns - set(optional_columns)
            if critical_missing:
                logger.error(f"Critical columns missing: {critical_missing}")
                return False
            else:
                if missing_columns:
                    logger.info(
                        f"Optional columns missing, will use defaults: {missing_columns}")
        return True

    def batch_predict(self, df: pd.DataFrame) -> List[Tuple[str, float]]:
        """Make predictions for multiple samples efficiently"""
        try:
            if not self.validate_input_format(df):
                raise ValueError("Invalid input format")

            features = self.preprocess_data(df)

            if self.model is None:
                raise ValueError("Model not loaded")

            # Make batch predictions (more efficient than individual predictions)
            batch_predictions = self.model.predict(features)

            # Get batch probabilities if available
            if hasattr(self.model, 'predict_proba'):
                batch_probabilities = self.model.predict_proba(features)
                confidences = np.max(batch_probabilities, axis=1)
            elif hasattr(self.model, 'decision_function'):
                decision_scores = self.model.decision_function(features)
                confidences = 1 / (1 + np.exp(-np.abs(decision_scores)))
            else:
                confidences = np.full(len(batch_predictions), 0.8)

            # Map predictions to strings
            prediction_map = {
                0: "FALSE POSITIVE",
                1: "CONFIRMED",
                2: "CANDIDATE",
                "FALSE POSITIVE": "FALSE POSITIVE",
                "CONFIRMED": "CONFIRMED",
                "CANDIDATE": "CANDIDATE"
            }

            predictions = []
            for i, pred in enumerate(batch_predictions):
                pred_str = prediction_map.get(pred, f"UNKNOWN({pred})")
                conf = float(confidences[i])
                predictions.append((pred_str, conf))

            logger.info(
                f"Completed batch prediction for {len(predictions)} samples")
            return predictions

        except Exception as e:
            logger.error(f"Error in batch prediction: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise

    def retrain_with_feedback(self, training_data: pd.DataFrame) -> None:
        """Retrain model with new feedback data (placeholder)"""
        # This would implement model retraining logic
        # For now, just log the request
        logger.info(
            f"Model retraining requested with {len(training_data)} samples")
        # TODO: Implement actual retraining logic


# Global instance for dependency injection
_ml_model_instance = None


def get_ml_model() -> ExoplanetMLModel:
    """Get ML model instance (singleton pattern)"""
    global _ml_model_instance
    if _ml_model_instance is None:
        _ml_model_instance = ExoplanetMLModel()
    return _ml_model_instance
