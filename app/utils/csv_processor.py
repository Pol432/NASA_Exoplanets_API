import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from fastapi import HTTPException, status
import logging
from io import StringIO

logger = logging.getLogger(__name__)


class CSVProcessor:

    # Core required columns from the CSV format you provided
    REQUIRED_COLUMNS = [
        'koi_period', 'koi_depth', 'koi_duration', 'koi_impact',
        'koi_insol', 'koi_model_snr', 'koi_steff', 'koi_slogg',
        'koi_srad', 'ra', 'dec', 'koi_kepmag', 'koi_score'
    ]

    OPTIONAL_COLUMNS = [
        'kepid', 'kepoi_name', 'kepler_name', 'koi_time0bk', 'koi_prad',
        'koi_tce_plnt_num', 'koi_disposition', 'koi_pdisposition', 'koi_teq',
        # Flag columns from your CSV format
        'koi_fpflag_nt', 'koi_fpflag_ss', 'koi_fpflag_co', 'koi_fpflag_ec'
    ]

    ERROR_COLUMNS = [
        'koi_period_err1', 'koi_period_err2', 'koi_time0bk_err1', 'koi_time0bk_err2',
        'koi_impact_err1', 'koi_impact_err2', 'koi_duration_err1', 'koi_duration_err2',
        'koi_depth_err1', 'koi_depth_err2', 'koi_prad_err1', 'koi_prad_err2',
        'koi_teq_err1', 'koi_teq_err2', 'koi_insol_err1', 'koi_insol_err2',
        'koi_steff_err1', 'koi_steff_err2', 'koi_slogg_err1', 'koi_slogg_err2',
        'koi_srad_err1', 'koi_srad_err2'
    ]

    @classmethod
    def validate_csv_format(cls, df: pd.DataFrame) -> Dict[str, any]:
        """Validate CSV format and return validation results"""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "missing_required": [],
            "missing_optional": [],
            "extra_columns": [],
            "data_quality_issues": []
        }

        # Check for required columns
        missing_required = set(cls.REQUIRED_COLUMNS) - set(df.columns)
        if missing_required:
            validation_result["missing_required"] = list(missing_required)
            validation_result["valid"] = False
            validation_result["errors"].append(
                f"Missing required columns: {', '.join(missing_required)}"
            )

        # Check for optional columns (just log, don't fail)
        missing_optional = set(cls.OPTIONAL_COLUMNS) - set(df.columns)
        if missing_optional:
            validation_result["missing_optional"] = list(missing_optional)
            validation_result["warnings"].append(
                f"Missing optional columns: {', '.join(missing_optional)}"
            )

        # Missing error columns are acceptable
        missing_error = set(cls.ERROR_COLUMNS) - set(df.columns)
        if missing_error:
            validation_result["warnings"].append(
                f"Missing error columns (will be filled with 0): {', '.join(missing_error)}"
            )

        # Check for extra columns (informational only)
        all_expected = set(cls.REQUIRED_COLUMNS +
                           cls.OPTIONAL_COLUMNS + cls.ERROR_COLUMNS)
        extra_columns = set(df.columns) - all_expected
        if extra_columns:
            validation_result["extra_columns"] = list(extra_columns)
            logger.info(
                f"Extra columns found (will be ignored): {', '.join(extra_columns)}")

        # Data quality checks
        data_issues = cls._check_data_quality(df)
        validation_result["data_quality_issues"] = data_issues
        if data_issues:
            validation_result["warnings"].extend(data_issues)

        return validation_result

    @classmethod
    def _check_data_quality(cls, df: pd.DataFrame) -> List[str]:
        """Check for data quality issues"""
        issues = []

        # Check for excessive missing values
        for col in cls.REQUIRED_COLUMNS:
            if col in df.columns:
                missing_pct = df[col].isnull().sum() / len(df) * 100
                if missing_pct > 50:
                    issues.append(
                        f"Column '{col}' has {missing_pct:.1f}% missing values")

        # Check for invalid ranges
        range_checks = {
            'koi_period': (0, 10000),  # days
            # relative depth (no upper limit due to outliers)
            'koi_depth': (0, None),
            'koi_teq': (0, 5000),      # Kelvin
            'koi_steff': (2000, 10000),  # Kelvin
            'koi_srad': (0, 50),       # solar radii
            'ra': (0, 360),            # degrees
            'dec': (-90, 90),          # degrees
        }

        for col, (min_val, max_val) in range_checks.items():
            if col in df.columns:
                if max_val is not None:
                    out_of_range = ((df[col] < min_val) |
                                    (df[col] > max_val)).sum()
                else:
                    out_of_range = (df[col] < min_val).sum()

                if out_of_range > 0:
                    issues.append(
                        f"Column '{col}' has {out_of_range} values out of expected range")

        return issues

    @classmethod
    def process_csv_content(cls, content: bytes, filename: str) -> Tuple[pd.DataFrame, Dict]:
        """Process CSV content and return DataFrame with validation results"""
        try:
            # Try to decode content
            try:
                content_str = content.decode('utf-8')
            except UnicodeDecodeError:
                content_str = content.decode('latin-1')

            # Read CSV
            df = pd.read_csv(StringIO(content_str))

            # Log basic info
            logger.info(
                f"Processing CSV '{filename}' with {len(df)} rows and {len(df.columns)} columns")

            # Validate format
            validation_result = cls.validate_csv_format(df)

            if not validation_result["valid"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid CSV format: {'; '.join(validation_result['errors'])}"
                )

            # Clean and prepare data
            df_cleaned = cls._clean_dataframe(df)

            return df_cleaned, validation_result

        except pd.errors.EmptyDataError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CSV file is empty"
            )
        except pd.errors.ParserError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"CSV parsing error: {str(e)}"
            )
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            logger.error(f"Error processing CSV: {str(e)}")
            logger.error(f"Full traceback: {error_details}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error processing CSV file: {str(e)}"
            )

    @classmethod
    def _clean_dataframe(cls, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize the DataFrame"""
        df_clean = df.copy()

        # Convert numeric columns
        numeric_columns = cls.REQUIRED_COLUMNS + cls.ERROR_COLUMNS + [
            col for col in cls.OPTIONAL_COLUMNS
            if col not in ['kepoi_name', 'kepler_name', 'koi_disposition', 'koi_pdisposition']
        ]

        for col in numeric_columns:
            if col in df_clean.columns:
                df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')

        # Handle infinite values
        df_clean.replace([np.inf, -np.inf], np.nan, inplace=True)

        # Clean string columns
        string_columns = ['kepoi_name', 'kepler_name',
                          'koi_disposition', 'koi_pdisposition']
        for col in string_columns:
            if col in df_clean.columns:
                df_clean[col] = df_clean[col].astype(str).str.strip()
                df_clean[col] = df_clean[col].replace('nan', np.nan)

        # Add missing error columns with 0 values
        for err_col in cls.ERROR_COLUMNS:
            if err_col not in df_clean.columns:
                df_clean[err_col] = 0.0
                logger.info(
                    f"Added missing error column '{err_col}' with default value 0")

        # If kepid is missing, generate sequential IDs
        if 'kepid' not in df_clean.columns:
            df_clean['kepid'] = range(1, len(df_clean) + 1)
            logger.warning("kepid column missing, generated sequential IDs")

        return df_clean

    @classmethod
    def validate_for_ml_prediction(cls, df: pd.DataFrame) -> bool:
        """Validate DataFrame for ML model prediction"""
        ml_required_features = [
            'koi_period', 'koi_time0bk', 'koi_impact', 'koi_duration', 'koi_depth',
            'koi_prad', 'koi_teq', 'koi_insol', 'koi_model_snr', 'koi_tce_plnt_num',
            'koi_steff', 'koi_slogg', 'koi_srad', 'ra', 'dec', 'koi_kepmag', 'koi_score'
        ]

        missing_features = set(ml_required_features) - set(df.columns)

        if missing_features:
            logger.warning(f"Missing ML features: {missing_features}")
            return False

        # Check if we have enough non-null values for prediction
        critical_features = ['koi_period', 'koi_depth',
                             'koi_duration', 'koi_steff', 'koi_score']
        for feature in critical_features:
            if df[feature].isnull().all():
                logger.warning(
                    f"Critical feature '{feature}' is completely null")
                return False

        return True

    @classmethod
    def prepare_for_database(cls, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare DataFrame for database insertion"""
        df_db = df.copy()

        # Ensure all expected columns exist
        all_columns = cls.REQUIRED_COLUMNS + cls.OPTIONAL_COLUMNS + cls.ERROR_COLUMNS
        for col in all_columns:
            if col not in df_db.columns:
                df_db[col] = None

        # Convert NaN to None for database
        df_db = df_db.where(pd.notna(df_db), None)

        # Include all columns that are in the database schema (including flag columns)
        return df_db[[col for col in all_columns if col in df_db.columns]]
