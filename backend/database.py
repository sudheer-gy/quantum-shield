import os
from supabase import create_client, Client

# These load the secrets we will save in Render momentarily
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

def get_db_connection():
    if not url or not key:
        print("Error: Supabase credentials missing.")
        return None
    try:
        # Create the connection
        supabase: Client = create_client(url, key)
        return supabase
    except Exception as e:
        print(f"Supabase Connection Error: {e}")
        return None