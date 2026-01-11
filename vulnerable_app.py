# vulnerable_app.py
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES

def generate_legacy_keys():
    # BAD: RSA is vulnerable to Shor's Algorithm (Quantum Computers)
    # This is exactly what we want our tool to find.
    key = RSA.generate(2048)
    
    with open('private.pem', 'wb') as f:
        f.write(key.export_key())

def weak_encryption():
    # BAD: AES-128 is "okay" today, but AES-256 is required for Quantum resistance
    # (Grover's Algorithm reduces effective security by half)
    cipher = AES.new(b'1234567890123456', AES.MODE_ECB) 
    return cipher