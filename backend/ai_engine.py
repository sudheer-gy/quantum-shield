from google import genai
from google.genai import types
import os
import time

def fix_code(vulnerability_type, code_snippet):
    api_key = os.environ.get("GEMINI_API_KEY")
    
    if not api_key:
        return "Error: Server missing API Key."

    try:
        # Initialize Client
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

        # We use 'gemini-flash-latest' because it always points to the 
        # model with the best available free tier quota.
        # We also add a simple retry mechanism for reliability.
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(
                    model='gemini-flash-latest',
                    contents=prompt
                )
                
                if response.text:
                    return response.text.replace('```python', '').replace('```java', '').replace('```', '').strip()
            
            except Exception as e:
                # If it's a "Too Many Requests" error, wait and retry
                if "429" in str(e) and attempt < max_retries - 1:
                    time.sleep(2)  # Wait 2 seconds
                    continue
                else:
                    raise e # Throw the error if we can't fix it

        return "Error: AI returned empty response."

    except Exception as e:
        return f"AI Error: {str(e)}"