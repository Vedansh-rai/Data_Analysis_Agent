"""
Auto Dashboard Generator
Automatically creates interactive Plotly charts based on data analysis.
"""
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, List, Any, Optional
import json


class AutoDashboard:
    """
    Generates interactive Plotly visualizations automatically based on data analysis.
    """
    
    def __init__(self):
        self.color_palette = px.colors.qualitative.Set2
    
    def analyze_columns(self, df: pd.DataFrame) -> Dict[str, List[str]]:
        """Categorize columns by type for smart visualization selection."""
        analysis = {
            "numeric": [],
            "categorical": [],
            "datetime": [],
            "text": []
        }
        
        for col in df.columns:
            # Try to detect datetime
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                analysis["datetime"].append(col)
            elif 'date' in col.lower() or 'time' in col.lower():
                try:
                    pd.to_datetime(df[col])
                    analysis["datetime"].append(col)
                except:
                    pass
            elif pd.api.types.is_numeric_dtype(df[col]):
                analysis["numeric"].append(col)
            elif df[col].nunique() <= 20:  # Low cardinality = categorical
                analysis["categorical"].append(col)
            else:
                analysis["text"].append(col)
        
        return analysis
    
    def generate_dashboard(self, df: pd.DataFrame, filename: str) -> Dict[str, Any]:
        """
        Generate a complete dashboard with multiple auto-selected charts.
        Returns chart specs as Plotly JSON for frontend rendering.
        """
        col_analysis = self.analyze_columns(df)
        charts = []
        
        # 1. Distribution chart for first numeric column
        if col_analysis["numeric"]:
            chart = self._create_histogram(df, col_analysis["numeric"][0])
            charts.append({"type": "histogram", "title": chart["title"], "data": chart["json"]})
        
        # 2. Bar chart: Categorical vs Numeric
        if col_analysis["categorical"] and col_analysis["numeric"]:
            chart = self._create_bar_chart(
                df, 
                col_analysis["categorical"][0], 
                col_analysis["numeric"][0]
            )
            charts.append({"type": "bar", "title": chart["title"], "data": chart["json"]})
        
        # 3. Line chart: Time series (if datetime exists)
        if col_analysis["datetime"] and col_analysis["numeric"]:
            chart = self._create_line_chart(
                df,
                col_analysis["datetime"][0],
                col_analysis["numeric"][0]
            )
            charts.append({"type": "line", "title": chart["title"], "data": chart["json"]})
        
        # 4. Scatter plot: Two numeric columns
        if len(col_analysis["numeric"]) >= 2:
            chart = self._create_scatter(
                df,
                col_analysis["numeric"][0],
                col_analysis["numeric"][1],
                col_analysis["categorical"][0] if col_analysis["categorical"] else None
            )
            charts.append({"type": "scatter", "title": chart["title"], "data": chart["json"]})
        
        # 5. Pie chart for categorical distribution
        if col_analysis["categorical"]:
            chart = self._create_pie_chart(df, col_analysis["categorical"][0])
            charts.append({"type": "pie", "title": chart["title"], "data": chart["json"]})
        
        # 6. Correlation heatmap
        if len(col_analysis["numeric"]) >= 2:
            chart = self._create_correlation_heatmap(df, col_analysis["numeric"])
            if chart:
                charts.append({"type": "heatmap", "title": chart["title"], "data": chart["json"]})
        
        return {
            "filename": filename,
            "chart_count": len(charts),
            "charts": charts,
            "column_types": col_analysis
        }
    
    def _create_histogram(self, df: pd.DataFrame, col: str) -> Dict:
        """Create a histogram for numeric distribution."""
        fig = px.histogram(
            df, x=col, 
            title=f"Distribution of {col}",
            color_discrete_sequence=self.color_palette,
            template="plotly_dark"
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='#f1f5f9'
        )
        return {"title": f"Distribution of {col}", "json": fig.to_json()}
    
    def _create_bar_chart(self, df: pd.DataFrame, cat_col: str, num_col: str) -> Dict:
        """Create a bar chart for category comparison."""
        # Aggregate
        agg_df = df.groupby(cat_col)[num_col].sum().reset_index()
        agg_df = agg_df.sort_values(num_col, ascending=False).head(15)
        
        fig = px.bar(
            agg_df, x=cat_col, y=num_col,
            title=f"{num_col} by {cat_col}",
            color=num_col,
            color_continuous_scale="Blues",
            template="plotly_dark"
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='#f1f5f9'
        )
        return {"title": f"{num_col} by {cat_col}", "json": fig.to_json()}
    
    def _create_line_chart(self, df: pd.DataFrame, date_col: str, num_col: str) -> Dict:
        """Create a line chart for time series."""
        df_copy = df.copy()
        try:
            df_copy[date_col] = pd.to_datetime(df_copy[date_col])
            agg_df = df_copy.groupby(date_col)[num_col].sum().reset_index()
            agg_df = agg_df.sort_values(date_col)
        except:
            agg_df = df_copy
        
        fig = px.line(
            agg_df, x=date_col, y=num_col,
            title=f"{num_col} Over Time",
            template="plotly_dark",
            markers=True
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='#f1f5f9'
        )
        return {"title": f"{num_col} Over Time", "json": fig.to_json()}
    
    def _create_scatter(self, df: pd.DataFrame, x_col: str, y_col: str, color_col: Optional[str] = None) -> Dict:
        """Create a scatter plot."""
        sample_df = df.sample(min(1000, len(df)))  # Sample for performance
        
        fig = px.scatter(
            sample_df, x=x_col, y=y_col,
            color=color_col if color_col else None,
            title=f"{y_col} vs {x_col}",
            template="plotly_dark",
            opacity=0.7
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='#f1f5f9'
        )
        return {"title": f"{y_col} vs {x_col}", "json": fig.to_json()}
    
    def _create_pie_chart(self, df: pd.DataFrame, cat_col: str) -> Dict:
        """Create a pie chart for category distribution."""
        value_counts = df[cat_col].value_counts().head(10)
        
        fig = px.pie(
            values=value_counts.values,
            names=value_counts.index,
            title=f"Distribution of {cat_col}",
            template="plotly_dark",
            color_discrete_sequence=self.color_palette
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='#f1f5f9'
        )
        return {"title": f"Distribution of {cat_col}", "json": fig.to_json()}
    
    def _create_correlation_heatmap(self, df: pd.DataFrame, numeric_cols: List[str]) -> Optional[Dict]:
        """Create a correlation heatmap."""
        if len(numeric_cols) < 2:
            return None
        
        corr_matrix = df[numeric_cols].corr()
        
        fig = px.imshow(
            corr_matrix,
            title="Correlation Heatmap",
            template="plotly_dark",
            color_continuous_scale="RdBu_r",
            aspect="auto"
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='#f1f5f9'
        )
        return {"title": "Correlation Heatmap", "json": fig.to_json()}
    
    def create_custom_chart(
        self, 
        df: pd.DataFrame, 
        x_col: str, 
        y_col: str, 
        chart_type: str = "bar",
        color_col: str = None,
        aggregation: str = "sum"
    ) -> Dict[str, Any]:
        """
        Create a custom chart based on user selections (like Tableau).
        """
        # Sample for performance
        sample_df = df.copy()
        if len(df) > 5000:
            sample_df = df.sample(5000)
        
        # Apply aggregation if needed
        if aggregation and chart_type in ["bar", "line"]:
            agg_func = {
                "sum": "sum",
                "mean": "mean",
                "count": "count",
                "min": "min",
                "max": "max"
            }.get(aggregation, "sum")
            
            if color_col and color_col != "None":
                agg_df = df.groupby([x_col, color_col])[y_col].agg(agg_func).reset_index()
            else:
                agg_df = df.groupby(x_col)[y_col].agg(agg_func).reset_index()
                color_col = None
            sample_df = agg_df
        
        # Create chart based on type
        color_param = color_col if color_col and color_col != "None" else None
        
        if chart_type == "bar":
            fig = px.bar(
                sample_df, x=x_col, y=y_col, color=color_param,
                title=f"{aggregation.upper()} of {y_col} by {x_col}",
                template="plotly_dark",
                color_discrete_sequence=self.color_palette
            )
        elif chart_type == "line":
            fig = px.line(
                sample_df.sort_values(x_col), x=x_col, y=y_col, color=color_param,
                title=f"{y_col} Trend by {x_col}",
                template="plotly_dark",
                markers=True
            )
        elif chart_type == "scatter":
            fig = px.scatter(
                sample_df, x=x_col, y=y_col, color=color_param,
                title=f"{y_col} vs {x_col}",
                template="plotly_dark",
                opacity=0.7
            )
        elif chart_type == "pie":
            value_counts = df[x_col].value_counts().head(15)
            fig = px.pie(
                values=value_counts.values,
                names=value_counts.index,
                title=f"Distribution of {x_col}",
                template="plotly_dark",
                color_discrete_sequence=self.color_palette
            )
        elif chart_type == "histogram":
            fig = px.histogram(
                sample_df, x=x_col, color=color_param,
                title=f"Distribution of {x_col}",
                template="plotly_dark",
                color_discrete_sequence=self.color_palette
            )
        elif chart_type == "box":
            fig = px.box(
                sample_df, x=x_col if color_param else None, y=y_col, color=color_param,
                title=f"Distribution of {y_col}",
                template="plotly_dark"
            )
        elif chart_type == "area":
            fig = px.area(
                sample_df.sort_values(x_col), x=x_col, y=y_col, color=color_param,
                title=f"{y_col} Area by {x_col}",
                template="plotly_dark"
            )
        else:
            fig = px.bar(sample_df, x=x_col, y=y_col, template="plotly_dark")
        
        # Common layout updates
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='#f1f5f9',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        return {
            "type": chart_type,
            "title": fig.layout.title.text if fig.layout.title else f"{y_col} by {x_col}",
            "data": fig.to_json()
        }
