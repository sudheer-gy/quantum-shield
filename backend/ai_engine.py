from google import genai
import os

def fix_code(vulnerability_type, code_snippet):
    api_key = os.environ.get("GEMINI_API_KEY")
    
    if not api_key:
        return "Error: Server missing API Key."

    try:
        # NEW SYNTAX: Initialize the Client
        client = genai.Client(api_key=api_key)
        
        prompt = f"""
        You are a Cybersecurity Expert.
        The user has code with this vulnerability: "{vulnerability_type}"
        
        Here is the vulnerable code snippet:
        ```
        {code_snippet}
        ```
        
        TASK:
        Rewrite this code to be QUANTUM-SECURE. 
        - Provide ONLY the code. Do not write explanations. 
        """

        # Call the model (Using the latest stable flash model)
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=prompt
        )
        
        return response.text.replace('```python', '').replace('```java', '').replace('```', '').strip()

    except Exception as e:
        return f"AI Error: {str(e)}"