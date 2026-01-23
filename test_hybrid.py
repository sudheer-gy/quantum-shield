import hashlib
import os

# ?? BUG 1: QUANTUM VULNERABILITY (MD5)
def get_quantum_unsafe_hash(data):
    return hashlib.md5(data.encode()).hexdigest()

# ?? BUG 2: STANDARD VULNERABILITY (Hardcoded Password)
def connect_to_database():
    password = "super_secret_password_123" 
    print(f"Connecting with {password}")
