"""
Script to test the OpenRouter model token limits with larger models
"""
import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the current directory to the path so we can import from app
sys.path.insert(0, os.path.abspath('.'))

# Load environment variables
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

# Now import the components
from app.core.config import settings
from app.services.llm import OpenRouterClient

async def test_token_limits():
    """Test the token limits for different models on OpenRouter"""
    print("\n===== OPENROUTER TOKEN LIMITS TEST =====\n")
    
    # Create the client
    client = OpenRouterClient()
    
    # Get current model from settings
    current_model = settings.DEFAULT_LLM_MODEL
    print(f"Current model: {current_model}")
    print(f"LLM max tokens setting: {settings.LLM_MAX_TOKENS}")
    
    # Test models to check limits
    models_to_test = [
        current_model,
        "meta-llama/llama-3-70b-instruct"
    ]
    
    # Print model limits
    print("\n----- MODEL LIMITS -----")
    for model in models_to_test:
        limit = client.get_max_token_limit(model)
        print(f"{model}: {limit} tokens max output")
    
    # Generate a long prompt that will test the output token limits
    long_prompt = """
    Write a comprehensive explanation about large language models (LLMs) and their applications.
    Include these sections:
    1. Introduction to LLMs
    2. How LLMs work (include details on architecture, training, and inference)
    3. Different types of LLMs (include at least 3 major model families)
    4. Applications in various industries (at least 5 industries with specific use cases)
    5. Ethical considerations and challenges
    6. Future directions and research
    
    Make each section detailed with examples and data. The response should be comprehensive
    and demonstrate the model's capabilities with longer text generation.
    """
    
    # Test the output generation with llama-3-70b-instruct
    print(f"\n----- TESTING meta-llama/llama-3-70b-instruct WITH MAX_TOKENS={settings.LLM_MAX_TOKENS} -----")
    print("Generating response. This may take a minute...")
    
    try:
        import time
        start_time = time.time()
        
        # Generate text with high max_tokens to test the limit
        response = await client.generate_text(
            long_prompt, 
            model="meta-llama/llama-3-70b-instruct",
            max_tokens=settings.LLM_MAX_TOKENS
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Count words and estimate tokens
        word_count = len(response.split())
        token_estimate = int(word_count * 1.3)
        
        print(f"\nResponse Statistics:")
        print(f"- Words: {word_count}")
        print(f"- Estimated tokens: {token_estimate}")
        print(f"- Generation time: {duration:.2f} seconds")
        print(f"- Tokens per second: {int(token_estimate/duration) if duration > 0 else 'N/A'}")
        
        # Check if the response seems truncated
        if token_estimate > (settings.LLM_MAX_TOKENS * 0.95):
            print("\n⚠️ Response appears to be at or near the token limit, may be truncated")
        else:
            print("\n✅ Response completed without reaching token limit")
        
        # Print the first 100 words and last 100 words
        first_100_words = " ".join(response.split()[:100]) + "..."
        last_100_words = "..." + " ".join(response.split()[-100:])
        
        print("\nFirst 100 words:")
        print(first_100_words)
        
        print("\nLast 100 words:")
        print(last_100_words)
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    print("\n===== TOKEN LIMIT TEST COMPLETE =====")
    print("Note: There's no actual cost for using llama-3-70b-instruct through OpenRouter")
    print("as they pass through the provider's pricing which incurs real costs.")
    print("This means there's no 'free' usage - you pay per token for input and output")
    print("according to OpenRouter's pricing model, even for open source models like Llama.")

async def main():
    await test_token_limits()

if __name__ == "__main__":
    asyncio.run(main()) 