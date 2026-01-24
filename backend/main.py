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

@app.get("/", response_class=HTMLResponse)
def home():
    return "<h1>Quantum Shield Backend is Running</h1>"

# --- ☢️ GOD MODE DEBUG ENDPOINT ---
@app.get("/test-internal")
def test_internal_scan():
    # 1. Python writes the Rules File directly (Guaranteed Correct Formatting)
    rules_content = """rules:
  - id: auto-generated-md5-rule
    patterns:
      - pattern: hashlib.md5(...)
    message: "CRITICAL: MD5 detected (God Mode verified)"
    languages: [python]
    severity: ERROR
"""
    with open("force_rules.yaml", "w") as f:
        f.write(rules_content)

    # 2. Python writes the Vulnerable Code directly
    code_content = """import hashlib
def bad_code():
    # This MUST trigger the rule above
    return hashlib.md5(b'123').hexdigest()
"""
    with open("force_test.py", "w") as f:
        f.write(code_content)
    
    # 3. Scan using the forced files
    print("🕵️‍♂️ GOD MODE: Running scan with forced rules...")
    command = ["semgrep", "scan", "--config=force_rules.yaml", "force_test.py", "--json"]
    result = subprocess.run(command, capture_output=True, text=True)
    
    # Debug Output
    print(f"📄 STDOUT: {result.stdout[:500]}")
    print(f"⚠️ STDERR: {result.stderr}")
    
    return json.loads(result.stdout)

# ---------------------------------------------------------
# REGULAR SCAN ENDPOINTS
# ---------------------------------------------------------
@app.post("/scan")
async def scan_code(file: UploadFile = File(...)):
    temp_filename = f"temp_{file.filename}"
    with open(temp_filename, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    results = run_semgrep(temp_filename)
    
    # DB Save
    try:
        supabase = get_db_connection()
        if supabase:
            data = {"filename": file.filename, "vulnerability_count": len(results.get("results", [])), "risk_level": "High"}
            supabase.table("scans").insert(data).execute()
    except Exception as e:
        print(f"❌ DB Error: {e}")

    if os.path.exists(temp_filename):
        os.remove(temp_filename)
    return results

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

@app.post("/fix")
async def get_ai_fix(request: FixRequest):
    return {"fixed_code": fix_code(request.issue, request.code)}

@app.post("/scan-repo")
async def scan_repo(request: RepoRequest):
    folder_name = f"temp_repo_{uuid.uuid4()}"
    try:
        subprocess.run(["git", "clone", request.repo_url, folder_name], check=True)
        results = run_semgrep(folder_name)
        return results
    except Exception as e:
        return {"error": str(e)}
    finally:
        if os.path.exists(folder_name):
            shutil.rmtree(folder_name)

def run_semgrep(filename):
    # Use the FORCE rules if they exist, otherwise default
    config = "force_rules.yaml" if os.path.exists("force_rules.yaml") else "p/default"
    command = ["semgrep", "scan", f"--config={config}", filename, "--json"]
    result = subprocess.run(command, capture_output=True, text=True)
    try:
        return json.loads(result.stdout)
    except:
        return {"results": []}