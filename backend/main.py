from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import shutil
import os
import sys

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from opal import Opal

from typing import List
from pydantic import BaseModel

app = FastAPI(title="Data Analysis Agent API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for local dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for charts
os.makedirs("output/charts", exist_ok=True)
app.mount("/charts", StaticFiles(directory="output/charts"), name="charts")

# Initialize Opal
opal = Opal()

@app.get("/")
def read_root():
    return {"status": "Agent is running 🚀"}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        file_location = f"data/raw/{file.filename}"
        os.makedirs(os.path.dirname(file_location), exist_ok=True)
        
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        return {"filename": file.filename, "location": file_location, "message": "File uploaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class ChatRequest(BaseModel):
    filename: str
    message: str
    history: List[dict] = []

@app.post("/chat")
async def chat_with_data(request: ChatRequest):
    """
    Conversational endpoint. Processes natural language query against the dataset.
    """
    file_path = f"data/raw/{request.filename}"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        response = opal.process_chat(file_path, request.message)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/export/tableau")
async def export_tableau(filename: str = Form(...)):
    """
    Generates a Tableau .tds file for the uploaded dataset.
    """
    file_path = f"data/raw/{filename}"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        result = opal.export_tableau(file_path)
        if "error" in result:
             raise HTTPException(status_code=500, detail=result["error"])
             
        # Create a download response
        # In a real app we'd serve the file, here we return the path for local usage
        return {"status": "success", "file_url": result["path"], "message": f"Tableau file generated at {result['path']}"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/columns")
async def get_columns(filename: str):
    """Returns available columns and their types for a given file."""
    file_path = f"data/raw/{filename}"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    # Tiny optimization: We load the whole file just to get columns. 
    # In prod, we'd cache this metadata.
    opal.antigravity.load_data(file_path)
    return opal.antigravity.get_columns()

@app.post("/analyze")
async def analyze_data(
    filename: str = Form(...), 
    query: str = Form(""), 
    x_axis: str = Form(None), 
    y_axis: str = Form(None)
):
    """
    Run the Opal pipeline on the uploaded file.
    """
    file_path = f"data/raw/{filename}"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found. Please upload first.")
    
    try:
        # Run Opal Pipeline with custom config
        result = opal.run_pipeline(file_path, query, x_axis, y_axis)
        if "error" in result:
             raise HTTPException(status_code=400, detail=result["error"])
             
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
