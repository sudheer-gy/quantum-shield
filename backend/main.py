from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse
from database import get_db_connection
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import subprocess
import os
import shutil
import json
import uuid
from report_generator import generate_pdf
from ai_engine import fix_code

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class FixRequest(BaseModel):
    code: str
    issue: str

class RepoRequest(BaseModel):
    repo_url: str

# ---------------------------------------------------------
# 🏠 HOME ROUTE (Restores the Dashboard UI)
# ---------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def home():
    # Try to load the dashboard UI
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    # Fallback if running from a different folder
    elif os.path.exists("backend/index.html"):
        with open("backend/index.html", "r", encoding="utf-8") as f:
            return f.read()
    else:
        return "<h1>Quantum Shield Backend is Ready 🛡️ (index.html not found)</h1>"

# ---------------------------------------------------------
# 1. MAIN SCANNER (Auto-Generates Rules)
# ---------------------------------------------------------
@app.post("/scan")
async def scan_code(file: UploadFile = File(...)):
    # Save user's file
    temp_filename = f"temp_{file.filename}"
    with open(temp_filename, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Run Scan
    results = run_semgrep(temp_filename)
    
    # Save to Database
    try:
        supabase = get_db_connection()
        if supabase:
            vulnerabilities = results.get("results", [])
            data = {
                "filename": file.filename, 
                "vulnerability_count": len(vulnerabilities), 
                "risk_level": "High" if len(vulnerabilities) > 0 else "Low"
            }
            supabase.table("scans").insert(data).execute()
            print(f"✅ Saved scan for {file.filename}")
    except Exception as e:
        print(f"❌ DB Error: {e}")

    # Cleanup
    if os.path.exists(temp_filename):
        os.remove(temp_filename)
        
    return results

# ---------------------------------------------------------
# 2. PDF REPORT
# ---------------------------------------------------------
@app.post("/report")
async def get_report(file: UploadFile = File(...)):
    temp_filename = f"temp_report_{file.filename}"
    with open(temp_filename, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    scan_data = run_semgrep(temp_filename)
    
    pdf_filename = f"report_{file.filename}.pdf"
    output_path = f"/tmp/{pdf_filename}" if os.path.exists("/tmp") else pdf_filename
    
    generate_pdf(scan_data.get('results', []), filename=output_path)
    
    if os.path.exists(temp_filename):
        os.remove(temp_filename)
        
    return FileResponse(output_path, media_type='application/pdf', filename=pdf_filename)

# ---------------------------------------------------------
# 3. AI FIX & REPO SCAN
# ---------------------------------------------------------
@app.post("/fix")
async def get_ai_fix(request: FixRequest):
    return {"fixed_code": fix_code(request.issue, request.code)}

@app.post("/scan-repo")
async def scan_repo(request: RepoRequest):
    folder_name = f"temp_repo_{uuid.uuid4()}"
    try:
        subprocess.run(["git", "clone", request.repo_url, folder_name], check=True)
        results = run_semgrep(folder_name)
        
        # Save Repo Stats
        try:
            supabase = get_db_connection()
            if supabase:
                data = {
                    "filename": request.repo_url, 
                    "vulnerability_count": len(results.get("results", [])), 
                    "risk_level": "High"
                }
                supabase.table("scans").insert(data).execute()
        except:
            pass

        return results
    except Exception as e:
        return {"error": str(e)}
    finally:
        if os.path.exists(folder_name):
            shutil.rmtree(folder_name)

# ---------------------------------------------------------
# ⚙️ THE BULLETPROOF SCANNER ENGINE
# ---------------------------------------------------------
def run_semgrep(filename):
    print(f"🕵️‍♂️ Scanning {filename}...")

    # 1. FORCE-CREATE THE RULES FILE (This fixes the 'Clean Scan' bug forever)
    # We write the file FRESH every single time.
    rules_content = """rules:
  - id: quantum-weak-hash-md5
    patterns:
      - pattern: hashlib.md5(...)
    message: "🚨 QUANTUM RISK: MD5 is broken by quantum computers."
    languages: [python]
    severity: ERROR

  - id: standard-hardcoded-password
    patterns:
      - pattern: $X = "..."
      - pattern-inside: |
          def connect_to_database():
            ...
    message: "⚠️ SECURITY RISK: Hardcoded secret detected."
    languages: [python]
    severity: WARNING
"""
    with open("quantum_rules.yaml", "w") as f:
        f.write(rules_content)

    # 2. RUN THE SCAN (Standard + Quantum)
    command = [
        "semgrep", 
        "scan", 
        "--config=p/default", 
        "--config=quantum_rules.yaml", 
        filename, 
        "--json"
    ]
    
    result = subprocess.run(command, capture_output=True, text=True)
    
    # Debug Logs (Visible in Render)
    print(f"📄 Results: {result.stdout[:200]}...") 
    
    try:
        return json.loads(result.stdout)
    except:
        return {"results": []}