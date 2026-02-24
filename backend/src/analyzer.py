"""
Data Analysis Agent - Core Analyzer
Automatically analyzes any CSV/Excel dataset and generates insights.
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import json


@dataclass
class AnalysisReport:
    """Structured report from data analysis."""
    filename: str
    summary: Dict[str, Any]
    column_analysis: List[Dict[str, Any]]
    insights: List[str]
    warnings: List[str]
    correlations: Optional[Dict[str, float]]
    

class DataAnalyzer:
    """
    Universal Data Analyzer.
    Accepts any tabular data and produces comprehensive analysis.
    """
    
    def __init__(self):
        self.df: Optional[pd.DataFrame] = None
        self.filename: str = ""
    
    def load_data(self, file_path: str) -> bool:
        """Load CSV or Excel file."""
        try:
            if file_path.endswith('.csv'):
                self.df = pd.read_csv(file_path)
            elif file_path.endswith(('.xlsx', '.xls')):
                self.df = pd.read_excel(file_path)
            else:
                # Try CSV as default
                self.df = pd.read_csv(file_path)
            
            self.filename = file_path.split('/')[-1]
            print(f"✅ Loaded {self.filename}: {len(self.df)} rows, {len(self.df.columns)} columns")
            return True
        except Exception as e:
            print(f"❌ Failed to load data: {e}")
            return False
    
    def analyze(self) -> AnalysisReport:
        """Run comprehensive analysis on loaded data."""
        if self.df is None:
            raise ValueError("No data loaded. Call load_data() first.")
        
        insights = []
        warnings = []
        column_analysis = []
        
        # 1. Basic Summary
        summary = {
            "rows": len(self.df),
            "columns": len(self.df.columns),
            "memory_mb": round(self.df.memory_usage(deep=True).sum() / 1024 / 1024, 2),
            "duplicates": int(self.df.duplicated().sum()),
            "column_names": list(self.df.columns)
        }
        
        if summary["duplicates"] > 0:
            warnings.append(f"⚠️ Found {summary['duplicates']} duplicate rows ({round(summary['duplicates']/summary['rows']*100, 1)}% of data)")
        
        # 2. Column-by-Column Analysis
        for col in self.df.columns:
            col_info = self._analyze_column(col)
            column_analysis.append(col_info)
            
            # Generate insights per column
            if col_info["missing_pct"] > 20:
                warnings.append(f"⚠️ Column '{col}' has {col_info['missing_pct']}% missing values")
            
            if col_info["type"] == "numeric" and col_info.get("outliers", 0) > 0:
                insights.append(f"📊 '{col}' contains {col_info['outliers']} potential outliers")
        
        # 3. Correlation Analysis (for numeric columns)
        correlations = self._find_correlations()
        if correlations:
            for pair, corr in correlations.items():
                if abs(corr) > 0.7:
                    insights.append(f"🔗 Strong correlation ({corr:.2f}) between {pair}")
        
        # 4. Auto-generated Insights
        insights.extend(self._generate_insights(summary, column_analysis))
        
        return AnalysisReport(
            filename=self.filename,
            summary=summary,
            column_analysis=column_analysis,
            insights=insights,
            warnings=warnings,
            correlations=correlations
        )
    
    def _analyze_column(self, col: str) -> Dict[str, Any]:
        """Analyze a single column."""
        series = self.df[col]
        missing = series.isna().sum()
        missing_pct = round(missing / len(series) * 100, 1)
        
        info = {
            "name": col,
            "dtype": str(series.dtype),
            "missing": int(missing),
            "missing_pct": missing_pct,
            "unique": int(series.nunique())
        }
        
        # Numeric column
        if pd.api.types.is_numeric_dtype(series):
            info["type"] = "numeric"
            info["mean"] = round(series.mean(), 2) if not series.isna().all() else None
            info["median"] = round(series.median(), 2) if not series.isna().all() else None
            info["std"] = round(series.std(), 2) if not series.isna().all() else None
            info["min"] = float(series.min()) if not series.isna().all() else None
            info["max"] = float(series.max()) if not series.isna().all() else None
            
            # Outlier detection (IQR method)
            Q1, Q3 = series.quantile([0.25, 0.75])
            IQR = Q3 - Q1
            outliers = ((series < Q1 - 1.5 * IQR) | (series > Q3 + 1.5 * IQR)).sum()
            info["outliers"] = int(outliers)
            
        # Categorical/Text column
        elif pd.api.types.is_object_dtype(series) or pd.api.types.is_categorical_dtype(series):
            info["type"] = "categorical"
            top_values = series.value_counts().head(5).to_dict()
            info["top_values"] = {str(k): int(v) for k, v in top_values.items()}
            
        # DateTime column
        elif pd.api.types.is_datetime64_any_dtype(series):
            info["type"] = "datetime"
            info["min_date"] = str(series.min())
            info["max_date"] = str(series.max())
            info["date_range_days"] = (series.max() - series.min()).days
        
        else:
            info["type"] = "other"
        
        return info
    
    def _find_correlations(self) -> Dict[str, float]:
        """Find correlations between numeric columns."""
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
        
        if len(numeric_cols) < 2:
            return {}
        
        corr_matrix = self.df[numeric_cols].corr()
        correlations = {}
        
        for i, col1 in enumerate(numeric_cols):
            for col2 in numeric_cols[i+1:]:
                corr_val = corr_matrix.loc[col1, col2]
                if not np.isnan(corr_val):
                    correlations[f"{col1} ↔ {col2}"] = round(corr_val, 3)
        
        return correlations
    
    def _generate_insights(self, summary: Dict, columns: List[Dict]) -> List[str]:
        """Generate automatic insights from the analysis."""
        insights = []
        
        # Dataset size insight
        if summary["rows"] > 100000:
            insights.append(f"📈 Large dataset with {summary['rows']:,} rows - consider sampling for faster analysis")
        elif summary["rows"] < 100:
            insights.append(f"📉 Small dataset with only {summary['rows']} rows - statistical conclusions may be limited")
        
        # Column type distribution
        numeric_count = sum(1 for c in columns if c["type"] == "numeric")
        categorical_count = sum(1 for c in columns if c["type"] == "categorical")
        
        if numeric_count > 0:
            insights.append(f"📊 {numeric_count} numeric columns available for statistical analysis")
        if categorical_count > 0:
            insights.append(f"🏷️ {categorical_count} categorical columns available for grouping/segmentation")
        
        # High cardinality warning
        for col in columns:
            if col["type"] == "categorical" and col["unique"] > 100:
                insights.append(f"🔤 '{col['name']}' has high cardinality ({col['unique']} unique values) - may need encoding")
        
        return insights
    
    def generate_report_markdown(self, report: AnalysisReport) -> str:
        """Generate a Markdown report from analysis."""
        md = f"""# 📊 Data Analysis Report
## File: {report.filename}

---

## 1. Overview
| Metric | Value |
|--------|-------|
| Total Rows | {report.summary['rows']:,} |
| Total Columns | {report.summary['columns']} |
| Memory Usage | {report.summary['memory_mb']} MB |
| Duplicate Rows | {report.summary['duplicates']} |

---

## 2. Warnings
"""
        if report.warnings:
            for w in report.warnings:
                md += f"- {w}\n"
        else:
            md += "_No warnings detected._\n"
        
        md += "\n---\n\n## 3. Key Insights\n"
        for insight in report.insights:
            md += f"- {insight}\n"
        
        md += "\n---\n\n## 4. Column Details\n"
        for col in report.column_analysis:
            md += f"\n### {col['name']}\n"
            md += f"- **Type**: {col['type']} ({col['dtype']})\n"
            md += f"- **Missing**: {col['missing']} ({col['missing_pct']}%)\n"
            md += f"- **Unique Values**: {col['unique']}\n"
            
            if col['type'] == 'numeric':
                md += f"- **Mean**: {col.get('mean')}, **Median**: {col.get('median')}\n"
                md += f"- **Range**: {col.get('min')} → {col.get('max')}\n"
                if col.get('outliers', 0) > 0:
                    md += f"- **Outliers**: {col['outliers']}\n"
            
            elif col['type'] == 'categorical' and 'top_values' in col:
                md += "- **Top Values**:\n"
                for val, count in list(col['top_values'].items())[:5]:
                    md += f"  - {val}: {count}\n"
        
        if report.correlations:
            md += "\n---\n\n## 5. Correlations\n"
            md += "| Column Pair | Correlation |\n|------------|-------------|\n"
            sorted_corr = sorted(report.correlations.items(), key=lambda x: abs(x[1]), reverse=True)
            for pair, corr in sorted_corr[:10]:
                strength = "🔴 Strong" if abs(corr) > 0.7 else "🟡 Moderate" if abs(corr) > 0.4 else "🟢 Weak"
                md += f"| {pair} | {corr} ({strength}) |\n"
        
        md += "\n---\n\n*Report generated by Data Analysis Agent*\n"
        return md


# Quick CLI usage
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python analyzer.py <path_to_csv>")
        sys.exit(1)
    
    analyzer = DataAnalyzer()
    if analyzer.load_data(sys.argv[1]):
        report = analyzer.analyze()
        print(analyzer.generate_report_markdown(report))
