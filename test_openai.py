import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv('/app/backend/.env')

# Print environment variables
print(f"OPENAI_API_KEY: {os.environ.get('OPENAI_API_KEY')}")

# Try to import OpenAI
try:
    from openai import OpenAI
    print("OpenAI package imported successfully")
    
    # Try to create a client
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    print("OpenAI client created successfully")
    
    # Try to make a simple API call
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello, world!"}
            ],
            max_tokens=10
        )
        print(f"API call successful: {response.choices[0].message.content}")
    except Exception as e:
        print(f"API call failed: {e}")
        
except ImportError as e:
    print(f"Failed to import OpenAI: {e}")
    
# Try to import httpx
try:
    import httpx
    print("httpx package imported successfully")
    
    # Try to create a client
    client = httpx.Client(timeout=10.0)
    print("httpx client created successfully")
    
except ImportError as e:
    print(f"Failed to import httpx: {e}")