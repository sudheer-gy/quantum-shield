from fastapi import FastAPI, UploadFile, File, Header, HTTPException, Depends
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from database import get_db_connection
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import subprocess
import os
import shutil
import json
import uuid
import hashlib # <--- NEW: For Security
from datetime import datetime
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

class KeyRequest(BaseModel):
    project_name: str

# ---------------------------------------------------------
# 🔐 SECURE API KEY LOGIC (Grok's Request)
# ---------------------------------------------------------
def hash_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()

@app.post("/generate-key")
def generate_api_key(req: KeyRequest):
    try:
        supabase = get_db_connection()
        if supabase:
            # 1. Generate Raw Key (Show this ONLY once)
            raw_key = f"qs_live_{uuid.uuid4().hex}"
            
            # 2. Hash it for storage (If DB is leaked, key is safe)
            key_hash = hash_key(raw_key)
            
            # 3. Save Hash to DB
            data = {"project_name": req.project_name, "key_value": key_hash}
            response = supabase.table("api_keys").insert(data).execute()
            
            if response.data:
                # Return RAW key to user (they must save it now)
                return {"api_key": raw_key, "project": req.project_name}
    except Exception as e:
        print(f"Key Gen Error: {e}")
        return {"error": "Failed to generate key"}
    return {"error": "Database error"}

def verify_api_key(x_api_key: str = Header(None)):
    if x_api_key:
        # Hash incoming key to compare with DB
        incoming_hash = hash_key(x_api_key)
        
        supabase = get_db_connection()
        # Look for the HASH, not the raw key
        response = supabase.table("api_keys").select("*").eq("key_value", incoming_hash).execute()
        
        if not response.data:
            raise HTTPException(status_code=401, detail="Invalid API Key")
            
        # Update last_used
        supabase.table("api_keys").update({"last_used_at": datetime.now().isoformat()}).eq("key_value", incoming_hash).execute()
        return response.data[0]
    return None 

# ---------------------------------------------------------
# 🏠 HOME & HISTORY
# ---------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def home():
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f: return f.read()
    elif os.path.exists("backend/index.html"):
        with open("backend/index.html", "r", encoding="utf-8") as f: return f.read()
    else: return "<h1>Quantum Shield Backend is Ready 🛡️</h1>"

@app.get("/history")
def get_history():
    try:
        supabase = get_db_connection()
        if supabase:
            response = supabase.table("scans").select("*").order("created_at", desc=True).limit(10).execute()
            return response.data
        return []
    except Exception as e:
        return []

# ---------------------------------------------------------
# 1. MAIN SCANNER
# ---------------------------------------------------------
@app.post("/scan")
async def scan_code(file: UploadFile = File(...), x_api_key: str = Header(None)):
    key_data = None
    if x_api_key:
        try:
            key_data = verify_api_key(x_api_key)
            print(f"🔑 Authenticated scan for project: {key_data['project_name']}")
        except:
            print("⚠️ Invalid API Key used")

    temp_filename = f"temp_{uuid.uuid4()}_{file.filename}"
    with open(temp_filename, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Run the upgraded engine
    results = run_semgrep(temp_filename)
    
    try:
        supabase = get_db_connection()
        if supabase:
            vulnerabilities = results.get("results", [])
            data = {
                "filename": file.filename, 
                "vulnerability_count": len(vulnerabilities), 
                "risk_level": "High" if len(vulnerabilities) > 0 else "Low",
                "api_key_id": key_data['id'] if key_data else None
            }
            supabase.table("scans").insert(data).execute()
    except Exception as e:
        print(f"❌ DB Error: {e}")

    if os.path.exists(temp_filename): os.remove(temp_filename)
    return results

# ---------------------------------------------------------
# REMAINING ROUTES (Report, Fix, Repo) - Unchanged
# ---------------------------------------------------------
@app.post("/report")
async def get_report(file: UploadFile = File(...)):
    temp_filename = f"temp_report_{file.filename}"
    with open(temp_filename, "wb") as buffer: shutil.copyfileobj(file.file, buffer)
    scan_data = run_semgrep(temp_filename)
    pdf_filename = f"report_{file.filename}.pdf"
    output_path = f"/tmp/{pdf_filename}" if os.path.exists("/tmp") else pdf_filename
    generate_pdf(scan_data.get('results', []), filename=output_path)
    if os.path.exists(temp_filename): os.remove(temp_filename)
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
        try:
            supabase = get_db_connection()
            if supabase:
                data = {
                    "filename": request.repo_url, 
                    "vulnerability_count": len(results.get("results", [])), 
                    "risk_level": "High"
                }
                supabase.table("scans").insert(data).execute()
        except: pass
        return results
    except Exception as e: return {"error": str(e)}
    finally:
        if os.path.exists(folder_name): shutil.rmtree(folder_name)

# ---------------------------------------------------------
# 🧠 THE ENGINE: NIST POST-QUANTUM RULES (v2.7)
# ---------------------------------------------------------
def run_semgrep(filename):
    print(f"🕵️‍♂️ Scanning {filename}...")
    
    # Updated Ruleset covering RSA, ECC, AES, and Secrets
    rules_content = """rules:
  # --- 1. LEGACY HASHES ---
  - id: quantum-weak-hash-md5-sha1
    patterns:
      - pattern-either:
          - pattern: hashlib.md5(...)
          - pattern: hashlib.sha1(...)
    message: "🚨 QUANTUM RISK: MD5/SHA1 are broken. Use SHA-3 or Shake256 (NIST Approved)."
    languages: [python]
    severity: ERROR

  # --- 2. ASYMMETRIC ENCRYPTION (The Big Ones) ---
  - id: quantum-weak-rsa
    patterns:
      - pattern-either:
          - pattern: Crypto.PublicKey.RSA.generate(...)
          - pattern: from Crypto.PublicKey import RSA
          - pattern: cryptography.hazmat.primitives.asymmetric.rsa.generate_private_key(...)
    message: "🚨 QUANTUM RISK: RSA is broken by Shor's Algorithm. Migrate to NIST PQC (CRYSTALS-Kyber)."
    languages: [python]
    severity: ERROR

  - id: quantum-weak-ecc-dh
    patterns:
      - pattern-either:
          - pattern: from cryptography.hazmat.primitives.asymmetric import ec
          - pattern: ecdsa.SigningKey.generate(...)
          - pattern: from pyDH import DiffieHellman
    message: "🚨 QUANTUM RISK: Elliptic Curve (ECC) and Diffie-Hellman are broken by quantum computers. Switch to Post-Quantum standards."
    languages: [python]
    severity: ERROR

  # --- 3. SYMMETRIC ENCRYPTION (Key Length) ---
  - id: quantum-weak-aes-128
    patterns:
      - pattern: AES.new($KEY, ...)
      - metavariable-pattern:
          metavariable: $KEY
          pattern-either:
            - pattern: b"..." 
    message: "⚠️ QUANTUM WARNING: AES-128 is weakened by Grover's Algorithm. NIST recommends AES-256 for long-term quantum resistance."
    languages: [python]
    severity: WARNING

  # --- 4. SECRETS (General Security) ---
  - id: standard-hardcoded-secret
    patterns:
      - pattern-either:
          - pattern: $X = "qs_live_..."
          - pattern: $X = "ghp_..."
          - pattern: $X = "sk_live_..."
    message: "⚠️ SECURITY RISK: Hardcoded API Key detected. Move to Environment Variables."
    languages: [python]
    severity: WARNING
"""
    with open("quantum_rules.yaml", "w") as f: f.write(rules_content)
    
    command = ["semgrep", "scan", "--config=p/default", "--config=quantum_rules.yaml", filename, "--json"]
    result = subprocess.run(command, capture_output=True, text=True)
    try: return json.loads(result.stdout)
    except: return {"results": []}