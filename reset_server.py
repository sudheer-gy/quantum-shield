import os

# 1. FORCE-WRITE clean rules (Fixes "Clean Scan")
clean_rules = """rules:
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

with open("quantum_rules.yaml", "w", encoding="utf-8") as f:
    f.write(clean_rules)
print("✅ quantum_rules.yaml reset to clean UTF-8.")

# 2. FORCE-WRITE a clean test file (Fixes "Clean Scan")
clean_test = """import hashlib
import os

def get_hash(data):
    # This triggers the MD5 rule
    return hashlib.md5(data.encode()).hexdigest()

def connect_to_database():
    # This triggers the Password rule
    password = "super_secret_password_123"
    print(f"Connecting with {password}")
"""

with open("test_clean.py", "w", encoding="utf-8") as f:
    f.write(clean_test)
print("✅ test_clean.py created.")

# 3. VERIFY Database Connection (Fixes "Database Error")
# This prints what the server actually sees (masked)
url = os.getenv("SUPABASE_URL")
if not url:
    print("❌ ERROR: SUPABASE_URL is NOT found in environment variables!")
else:
    print(f"✅ SUPABASE_URL found (starts with: {url[:8]}...)")