import google.generativeai as genai
import os

# Configure the AI with the key from the cloud "Safe"
def fix_code(vulnerability_type, code_snippet):
    api_key = os.environ.get("GEMINI_API_KEY")
    
    if not api_key:
        return "Error: Server missing API Key. Check Render Environment variables."

    try:
        genai.configure(api_key=api_key)
        # We use 'gemini-1.5-flash' because it is fast and free
        model = genai.GenerativeModel('gemini-1.5-flash')

        prompt = f"""
        You are a Top-Tier Cybersecurity Expert specializing in Post-Quantum Cryptography (PQC).
        
        The user has code with this vulnerability: "{vulnerability_type}"
        
        Here is the vulnerable code snippet:
        ```
        {code_snippet}
        ```
        
        TASK:
        Rewrite this code to be QUANTUM-SECURE. 
        - If it uses RSA/ECC, replace it with AES-256 (GCM) or a Quantum-Safe alternative.
        - Provide ONLY the code. Do not write explanations. 
        - If the snippet is too small to fix, provide a secure example of how that function should look.
        """

        response = model.generate_content(prompt)
        # Clean up the AI response to get just the code
        return response.text.replace('```python', '').replace('```java', '').replace('```', '').strip()

    except Exception as e:
        return f"AI Error: {str(e)}"