from google import genai
import os

# 1. PASTE YOUR KEY HERE (The one starting with AIzaSyBTP...)
MY_KEY = "AIzaSyBTPQjozbhNEJrVM85UNIZm-zqGyG2J0Pc" 

print(f"Testing Key: {MY_KEY[:10]}...")

try:
    client = genai.Client(api_key=MY_KEY)
    
    print("\n--- ASKING GOOGLE FOR AVAILABLE MODELS ---")
    # List all models available to your key
    for model in client.models.list():
        # Print the exact resource name we need
        print(f"✅ FOUND: {model.name}")
            
except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")