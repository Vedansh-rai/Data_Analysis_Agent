import altair as alt
import pandas as pd
from typing import Optional, Dict

class ChartEngine:
    """
    Handles generation of visualizations using Altair (Vega-Lite).
    """
    def __init__(self):
        pass

    def create_bar_chart(self, df: pd.DataFrame, x_col: str, y_col: str, title: str) -> Dict:
        """
        Creates a simple bar chart and returns the Vega-Lite JSON spec.
        """
        chart = alt.Chart(df).mark_bar().encode(
            x=alt.X(x_col, sort='-y'),
            y=y_col,
            tooltip=[x_col, y_col]
        ).properties(
            title=title
        ).interactive()
        
        return chart.to_dict()

    def create_line_chart(self, df: pd.DataFrame, x_col: str, y_col: str, title: str) -> Dict:
        """
        Creates a time-series line chart.
        """
        chart = alt.Chart(df).mark_line(point=True).encode(
            x=x_col,
            y=y_col,
            tooltip=[x_col, y_col]
        ).properties(
            title=title
        ).interactive()
        
        return chart.to_dict()

    def create_scatter_plot(self, df: pd.DataFrame, x_col: str, y_col: str, color_col: str = None, title: str = "") -> Dict:
        """
        Creates a scatter plot.
        """
        encoding = {
            "x": x_col,
            "y": y_col,
            "tooltip": [x_col, y_col]
        }
        if color_col:
            encoding["color"] = color_col

        chart = alt.Chart(df).mark_circle(size=60).encode(
            **encoding
        ).properties(
            title=title
        ).interactive()
        
        return chart.to_dict()

    def save_chart_json(self, chart_spec: Dict, output_path: str):
        """
        Saves the chart spec to a JSON file.
        """
        import json
        with open(output_path, 'w') as f:
            json.dump(chart_spec, f, indent=2)
            print(f"Details: Chart saved to {output_path}")

    # Note: PNG saving would require altair_saver/vl-convert, 
    # for now we stick to JSON/HTML which is the "Level Up" interactive part.
    def save_chart_html(self, chart_spec: Dict, output_path: str):
         """
         Saves the chart as an HTML file.
         """
         chart = alt.Chart.from_dict(chart_spec)
         chart.save(output_path)
         print(f"Details: Chart HTML saved to {output_path}")
