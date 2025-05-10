"""
Script to test the OpenRouter API connection
"""
import os
import sys
from dotenv import load_dotenv
from pathlib import Path
import logging
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the current directory to the path so we can import from app
sys.path.insert(0, os.path.abspath('.'))

# Load environment variables
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

# Now import the necessary components
from app.core.config import settings
from app.services.llm import OpenRouterClient

async def test_openrouter():
    """Test the OpenRouter API connection using async methods"""
    print(f"Testing OpenRouter API connection...")
    
    # Check if API key is set
    api_key = settings.OPENROUTER_API_KEY
    if not api_key:
        print("❌ OpenRouter API key is not set in the environment")
        return 1
    
    print(f"✅ OpenRouter API key is set: {api_key[:6]}...{api_key[-4:]}")
    
    # Create the client (no API key parameter needed as it reads from settings)
    client = OpenRouterClient()
    
    # Test with a simple query
    print("\nSending a test query to OpenRouter...")
    try:
        response = await client.chat_completion(
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say hello and identify yourself in one sentence."}
            ],
            temperature=0.7,
            max_tokens=100
        )
        
        if response and "choices" in response and response["choices"]:
            content = response["choices"][0]["message"]["content"]
            print(f"✅ Received response from OpenRouter: \"{content}\"")
            print(f"\nModel used: {response.get('model', 'unknown')}")
            return 0
        else:
            print(f"❌ Received empty or invalid response from OpenRouter: {response}")
            return 1
    except Exception as e:
        print(f"❌ Error connecting to OpenRouter: {str(e)}")
        return 1

def main():
    """Run the async test function"""
    return asyncio.run(test_openrouter())

if __name__ == "__main__":
    sys.exit(main()) 