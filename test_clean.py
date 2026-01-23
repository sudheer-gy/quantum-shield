import hashlib
import os

def get_hash(data):
    # This triggers the MD5 rule
    return hashlib.md5(data.encode()).hexdigest()

def connect_to_database():
    # This triggers the Password rule
    password = "super_secret_password_123"
    print(f"Connecting with {password}")
