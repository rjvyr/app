import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv('/app/backend/.env')

# Print environment variables
print(f"OPENAI_API_KEY: {os.environ.get('OPENAI_API_KEY')}")

# Try to import OpenAI
try:
    import openai
    print("OpenAI package imported successfully")
    print(f"OpenAI version: {openai.__version__}")
    
    # Set API key
    openai.api_key = os.environ.get("OPENAI_API_KEY")
    print("OpenAI API key set successfully")
    
    # Try to make a simple API call using the older client
    try:
        from openai import OpenAI
        
        # Create a custom HTTP client to avoid proxy issues
        import httpx
        http_client = httpx.Client(
            timeout=30.0,
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
        )
        
        # Create a new client with the custom HTTP client
        client = OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY"),
            http_client=http_client
        )
        
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
    print(f"httpx version: {httpx.__version__}")
    
except ImportError as e:
    print(f"Failed to import httpx: {e}")