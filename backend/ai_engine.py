from google import genai
import os

def fix_code(vulnerability_type, code_snippet):
    api_key = os.environ.get("GEMINI_API_KEY")
    
    if not api_key:
        return "Error: Server missing API Key."

    try:
        # Initialize the Client
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

        # Call the model (Using the specific '001' version for stability)
        response = client.models.generate_content(
            model='gemini-1.5-flash-001',
            contents=prompt
        )
        
        if response.text:
            return response.text.replace('```python', '').replace('```java', '').replace('```', '').strip()
        else:
            return "Error: AI returned empty response."

    except Exception as e:
        return f"AI Error: {str(e)}"