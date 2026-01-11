# backend/main.py
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import subprocess
import os
import shutil
import json

app = FastAPI()

# Allow the frontend to talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"status": "Quantum-Shield API is Online 🟢"}

@app.post("/scan")
async def scan_code(file: UploadFile = File(...)):
    # 1. Save the uploaded file temporarily
    temp_filename = f"temp_{file.filename}"
    
    with open(temp_filename, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # 2. Run the Engine (Semgrep)
    # We point it to the local rules file
    print(f"🔍 Scanning {temp_filename}...")
    
    command = [
        "semgrep", 
        "scan", 
        "--config=quantum_rules.yaml", 
        temp_filename, 
        "--json"
    ]
    
    # Run the command and capture output
    result = subprocess.run(command, capture_output=True, text=True)
    
    # 3. Clean up (delete the temp file)
    if os.path.exists(temp_filename):
        os.remove(temp_filename)
    
    # 4. Return the raw JSON to the frontend
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"error": "Failed to parse scan results", "raw_output": result.stderr}