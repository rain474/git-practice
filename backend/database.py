import os
from dotenv import load_dotenv

load_dotenv()

print("URL:", os.getenv("SUPABASE_URL"))
print("KEY exists:", os.getenv("SUPABASE_KEY") is not None)