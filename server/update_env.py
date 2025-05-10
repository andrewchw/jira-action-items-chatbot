#!/usr/bin/env python
"""
Script to update the LLM_MAX_TOKENS value in the .env file
"""
import os
from pathlib import Path
from dotenv import load_dotenv, set_key, find_dotenv

# Load environment variables from .env file
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

def update_max_tokens():
    """Update the LLM_MAX_TOKENS setting in .env file"""
    dotenv_file = find_dotenv()
    
    if not dotenv_file:
        print("Error: .env file not found. Creating a new one.")
        dotenv_file = str(env_path.absolute())
        # Ensure the file exists
        if not os.path.exists(dotenv_file):
            open(dotenv_file, 'a').close()
    
    # Get current value (if exists)
    current_value = os.getenv("LLM_MAX_TOKENS", "1023")
    
    try:
        # Set the new value (4096)
        set_key(dotenv_file, "LLM_MAX_TOKENS", "4096")
        print(f"✅ Updated LLM_MAX_TOKENS from {current_value} to 4096")
        
        # Add explanation comment to the file
        with open(dotenv_file, "r") as file:
            contents = file.readlines()
        
        # Find if there's already a value
        has_llm_max_tokens = any("LLM_MAX_TOKENS" in line for line in contents)
        
        # If not already explained, add an explanation
        if has_llm_max_tokens and not any("# Note on max tokens" in line for line in contents):
            with open(dotenv_file, "a") as file:
                file.write("\n# Note on max tokens: Most OpenRouter models support much higher token limits (8K-128K tokens).\n")
                file.write("# We've increased the default from 1023 to 4096 to allow for longer responses.\n")
        
        print("Added explanation to .env file")
        print("\nTo apply this change, restart your server or reload the application.")
    except Exception as e:
        print(f"❌ Error updating .env file: {str(e)}")

if __name__ == "__main__":
    update_max_tokens() 