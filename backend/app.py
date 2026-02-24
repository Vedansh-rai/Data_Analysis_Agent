"""
Data Analysis Agent - FastAPI Backend
Simple, reliable API for data analysis.
"""
import os
import sys
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import shutil
import pandas as pd

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from analyzer import DataAnalyzer

app = FastAPI(title="Data Analysis Agent")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure directories exist
os.makedirs("data/uploads", exist_ok=True)
os.makedirs("output/reports", exist_ok=True)

# Global analyzer instance
analyzer = DataAnalyzer()


@app.get("/")
async def root():
    return {"message": "Data Analysis Agent API", "status": "running"}


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a CSV or Excel file for analysis."""
    if not file.filename.endswith(('.csv', '.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Only CSV and Excel files are supported")
    
    file_path = f"data/uploads/{file.filename}"
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        return {
            "status": "success",
            "filename": file.filename,
            "location": file_path
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze")
async def analyze_file(filename: str):
    """Analyze an uploaded file and return comprehensive report."""
    file_path = f"data/uploads/{filename}"
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found. Please upload first.")
    
    try:
        # Load and analyze
        if not analyzer.load_data(file_path):
            raise HTTPException(status_code=500, detail="Failed to load data file")
        
        report = analyzer.analyze()
        
        # Generate markdown report
        markdown_report = analyzer.generate_report_markdown(report)
        
        # Save report
        report_path = f"output/reports/{filename.replace('.csv', '').replace('.xlsx', '')}_report.md"
        with open(report_path, 'w') as f:
            f.write(markdown_report)
        
        # Return structured response
        return {
            "status": "success",
            "filename": report.filename,
            "summary": report.summary,
            "column_analysis": report.column_analysis,
            "insights": report.insights,
            "warnings": report.warnings,
            "correlations": report.correlations,
            "report_markdown": markdown_report,
            "report_path": report_path
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/reports/{filename}")
async def get_report(filename: str):
    """Retrieve a saved report."""
    report_path = f"output/reports/{filename}"
    
    if not os.path.exists(report_path):
        raise HTTPException(status_code=404, detail="Report not found")
    
    with open(report_path, 'r') as f:
        content = f.read()
    
    return {"content": content}


# Import Tableau Connector
from tableau_connector import TableauConnector
tableau = TableauConnector()


@app.get("/tableau/check")
async def check_tableau():
    """Check if Tableau Desktop is installed."""
    return tableau.check_tableau_installed()


@app.post("/tableau/open")
async def open_in_tableau(filename: str):
    """Open an uploaded file in Tableau Desktop."""
    file_path = f"data/uploads/{filename}"
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found. Please upload first.")
    
    result = tableau.export_and_open(file_path, filename)
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to open Tableau"))
    
    return result


# Import Auto Dashboard Generator
from auto_dashboard import AutoDashboard
dashboard_generator = AutoDashboard()


@app.post("/dashboard")
async def generate_dashboard(filename: str):
    """
    Generate an interactive dashboard with auto-selected charts.
    Returns Plotly chart specs as JSON for frontend rendering.
    """
    file_path = f"data/uploads/{filename}"
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found. Please upload first.")
    
    try:
        # Load data
        if filename.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
        
        # Generate dashboard
        dashboard = dashboard_generator.generate_dashboard(df, filename)
        
        return dashboard
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chart/custom")
async def generate_custom_chart(
    filename: str,
    x_axis: str,
    y_axis: str,
    chart_type: str = "bar",
    color_by: str = None,
    aggregation: str = "sum"
):
    """
    Generate a custom chart based on user-selected parameters.
    Like Tableau's drag-and-drop interface.
    """
    file_path = f"data/uploads/{filename}"
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        # Load data
        if filename.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
        
        # Generate custom chart
        chart = dashboard_generator.create_custom_chart(
            df, x_axis, y_axis, chart_type, color_by, aggregation
        )
        
        return chart
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
