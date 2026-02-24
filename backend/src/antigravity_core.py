import pandas as pd
import numpy as np
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class DataIssue(BaseModel):
    column: str
    issue_type: str  # e.g., 'missing_values', 'wrong_type', 'outliers'
    description: str

class DatasetSummary(BaseModel):
    total_rows: int
    columns: List[str]
    missing_values: Dict[str, int]
    column_types: Dict[str, str]
    numeric_stats: Dict[str, Dict[str, float]]
    issues: List[DataIssue] = []

class Antigravity:
    """
    The Analytical Core: Handles data ingestion, validation, and basic statistical analysis.
    """
    def __init__(self):
        self.df: Optional[pd.DataFrame] = None
        self.summary: Optional[DatasetSummary] = None

    def load_data(self, file_path: str) -> bool:
        """
        Loads data from a CSV file.
        """
        try:
            # Try loading with default settings
            self.df = pd.read_csv(file_path)
            # Basic cleanup: strip whitespace from headers
            self.df.columns = self.df.columns.str.strip()
            print(f"Details: Loaded {len(self.df)} rows from {file_path}")
            return True
        except Exception as e:
            print(f"Error loading data: {e}")
            return False

    def analyze(self) -> DatasetSummary:
        """
        Performs a comprehensive analysis of the loaded dataset.
        """
        if self.df is None:
            raise ValueError("No data loaded. Call load_data() first.")

        issues = []
        
        # 1. Missing Values
        missing = self.df.isnull().sum().to_dict()
        for col, count in missing.items():
            if count > 0:
                issues.append(DataIssue(
                    column=col,
                    issue_type="missing_values",
                    description=f"{count} missing values found ({count/len(self.df):.1%})"
                ))

        # 2. Type Inference & Conversion Issues
        # (Simplified for MVP: just report current types)
        col_types = {col: str(dtype) for col, dtype in self.df.dtypes.items()}

        # 3. Numeric Stats
        numeric_stats = {}
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            desc = self.df[col].describe().to_dict()
            numeric_stats[col] = desc
            
            # Simple outlier detection (Z-score based for simplicity in MVP)
            # skipping complex detection for now to keep it lightweight
            
        self.summary = DatasetSummary(
            total_rows=len(self.df),
            columns=list(self.df.columns),
            missing_values=missing,
            column_types=col_types,
            numeric_stats=numeric_stats,
            issues=issues
        )
        
        return self.summary

    def get_columns(self) -> Dict[str, str]:
        """Returns column names and their types."""
        if self.df is None:
            return {}
        return {col: str(dtype) for col, dtype in self.df.dtypes.items()}

    def calculate_trend(self, target_col: str) -> Optional[str]:
        """
        Calculates a simple linear trend for a numeric column.
        Returns a string description of the trend.
        """
        if self.df is None or target_col not in self.df.columns:
            return None
        
        if not np.issubdtype(self.df[target_col].dtype, np.number):
            return None

        # Simple linear regression (y = mx + c) against index
        y = self.df[target_col].dropna()
        if len(y) < 2:
            return "Insufficient data for trend."
            
        x = np.arange(len(y))
        slope, intercept = np.polyfit(x, y, 1)
        
        trend = "stable"
        if slope > 0.05 * y.mean(): # Arbitrary threshold for significant change
            trend = "significantly increasing ↗️"
        elif slope > 0:
            trend = "slightly increasing ↗️"
        elif slope < -0.05 * y.mean():
            trend = "significantly decreasing ↘️"
        elif slope < 0:
            trend = "slightly decreasing ↘️"
            
        return f"Future Trend: {target_col} is {trend} (Slope: {slope:.2f})"

    def get_correlation_matrix(self) -> Dict[str, Any]:
        """Returns correlation matrix for numeric columns."""
        if self.df is None:
             return {}
        return self.df.select_dtypes(include=[np.number]).corr().to_dict()
