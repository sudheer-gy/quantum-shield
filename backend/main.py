from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse # <--- NEW IMPORT
from fastapi.middleware.cors import CORSMiddleware
import subprocess
import os
import shutil
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- THIS IS THE NEW PART ---
# Instead of returning text, we read the HTML file and send it to the browser.
@app.get("/", response_class=HTMLResponse)
def home():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()
# ----------------------------

@app.post("/scan")
async def scan_code(file: UploadFile = File(...)):
    temp_filename = f"temp_{file.filename}"
    
    with open(temp_filename, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Run Semgrep
    command = [
        "semgrep", 
        "scan", 
        "--config=quantum_rules.yaml", 
        temp_filename, 
        "--json"
    ]
    
    result = subprocess.run(command, capture_output=True, text=True)
    
    if os.path.exists(temp_filename):
        os.remove(temp_filename)
    
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"error": "Failed to parse scan results", "raw_output": result.stderr}