from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import subprocess
import os
import shutil
import json
from report_generator import generate_pdf
from ai_engine import fix_code  # <--- NEW IMPORT

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define the data format for AI requests
class FixRequest(BaseModel):
    code: str
    issue: str

@app.get("/", response_class=HTMLResponse)
def home():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

# 1. SCREEN SCAN (Returns JSON)
@app.post("/scan")
async def scan_code(file: UploadFile = File(...)):
    temp_filename = f"temp_{file.filename}"
    with open(temp_filename, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    results = run_semgrep(temp_filename)
    
    # Clean up
    if os.path.exists(temp_filename):
        os.remove(temp_filename)
        
    return results

# 2. PDF REPORT (Returns File)
@app.post("/report")
async def get_report(file: UploadFile = File(...)):
    # Save file
    temp_filename = f"temp_report_{file.filename}"
    with open(temp_filename, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # 1. Scan it
    scan_data = run_semgrep(temp_filename)
    
    # 2. Generate PDF
    # Use Helvetica via report_generator to avoid font errors
    pdf_filename = f"report_{file.filename}.pdf"
    # Detect environment (Cloud vs Local)
    output_path = f"/tmp/{pdf_filename}" if os.path.exists("/tmp") else pdf_filename
    
    generate_pdf(scan_data['results'], filename=output_path)
    
    # Clean up input file
    if os.path.exists(temp_filename):
        os.remove(temp_filename)
        
    # 3. Send PDF to user
    return FileResponse(output_path, media_type='application/pdf', filename=pdf_filename)

# 3. AI AUTO-FIX (NEW)
@app.post("/fix")
async def get_ai_fix(request: FixRequest):
    # Ask the AI Engine to rewrite the code
    fixed_code = fix_code(request.issue, request.code)
    return {"fixed_code": fixed_code}

# Helper function to run the command (Shared by both endpoints)
def run_semgrep(filename):
    command = [
        "semgrep", "scan", "--config=quantum_rules.yaml", filename, "--json"
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    try:
        return json.loads(result.stdout)
    except:
        return {"results": []}