from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse
from database import get_db_connection
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import subprocess
import os
import shutil
import json
import uuid  # For unique folder names
from report_generator import generate_pdf
from ai_engine import fix_code

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

# Define the data format for Repo requests
class RepoRequest(BaseModel):
    repo_url: str

@app.get("/", response_class=HTMLResponse)
def home():
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>Quantum Shield Backend is Running</h1>"

# 1. SCREEN SCAN (Returns JSON + SAVES TO DB)
@app.post("/scan")
async def scan_code(file: UploadFile = File(...)):
    # Save temp file
    temp_filename = f"temp_{file.filename}"
    with open(temp_filename, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Run the scan
    results = run_semgrep(temp_filename)
    
    # --- Save to Supabase ---
    try:
        # 1. Get stats
        vulnerabilities = results.get("results", [])
        risk_level = "High" if len(vulnerabilities) > 0 else "Low"
        
        # 2. Connect to DB
        supabase = get_db_connection()
        
        # 3. Insert Data
        if supabase:
            data = {
                "filename": file.filename,
                "vulnerability_count": len(vulnerabilities),
                "risk_level": risk_level
            }
            supabase.table("scans").insert(data).execute()
            print(f"✅ Saved scan for {file.filename} to Supabase!")
        else:
            print("⚠️ Database connection failed, skipping save.")
            
    except Exception as e:
        print(f"❌ Database Error: {e}")
    # -----------------------------

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
    pdf_filename = f"report_{file.filename}.pdf"
    output_path = f"/tmp/{pdf_filename}" if os.path.exists("/tmp") else pdf_filename
    
    generate_pdf(scan_data.get('results', []), filename=output_path)
    
    # Clean up input file
    if os.path.exists(temp_filename):
        os.remove(temp_filename)
        
    # 3. Send PDF to user
    return FileResponse(output_path, media_type='application/pdf', filename=pdf_filename)

# 3. AI AUTO-FIX
@app.post("/fix")
async def get_ai_fix(request: FixRequest):
    # Ask the AI Engine to rewrite the code
    fixed_code = fix_code(request.issue, request.code)
    return {"fixed_code": fixed_code}

# ---------------------------------------------------------
# 4. GITHUB REPO SCANNER
# ---------------------------------------------------------
@app.post("/scan-repo")
async def scan_repo(request: RepoRequest):
    repo_url = request.repo_url
    
    # 1. Create a unique folder name using UUID
    folder_name = f"temp_repo_{uuid.uuid4()}"
    
    try:
        print(f"📥 Cloning {repo_url}...")
        
        # 2. Clone the repo
        subprocess.run(["git", "clone", repo_url, folder_name], check=True)
        
        # 3. Run Semgrep on the ENTIRE folder
        print(f"🔍 Scanning {folder_name}...")
        results = run_semgrep(folder_name)
        
        # 4. Save Stats to Supabase
        try:
            vulnerabilities = results.get("results", [])
            risk_level = "High" if len(vulnerabilities) > 0 else "Low"
            supabase = get_db_connection()
            if supabase:
                data = {
                    "filename": repo_url,
                    "vulnerability_count": len(vulnerabilities),
                    "risk_level": risk_level
                }
                supabase.table("scans").insert(data).execute()
                print(f"✅ Saved repo scan for {repo_url}")
        except Exception as e:
            print(f"❌ DB Error: {e}")

        return results

    except Exception as e:
        return {"error": f"Failed to scan repo: {str(e)}"}
        
    finally:
        # 5. CLEANUP: Always delete the folder afterwards
        if os.path.exists(folder_name):
            shutil.rmtree(folder_name)
            print(f"🧹 Cleaned up {folder_name}")

# ---------------------------------------------------------
# HELPER: Semgrep Runner (UPDATED)
# ---------------------------------------------------------
def run_semgrep(filename):
    # 👇 UPDATED COMMAND:
    # 1. --config=p/default      <-- Standard Security Rules (OWASP, SANS)
    # 2. --config=quantum_rules.yaml <-- Your Custom Quantum Rules
    command = [
        "semgrep", 
        "scan", 
        "--config=p/default", 
        "--config=quantum_rules.yaml", 
        filename, 
        "--json"
    ]
    
    # Capture output and errors
    result = subprocess.run(command, capture_output=True, text=True)
    
    # Print errors to the console log if something goes wrong
    if result.returncode != 0:
        print(f"⚠️ Semgrep Warning/Error: {result.stderr}")

    try:
        return json.loads(result.stdout)
    except:
        return {"results": []}