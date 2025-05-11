#!/usr/bin/env python3
"""
Simple test script to verify our account ID validation logic works correctly
for the specific "deencat" account ID format.
"""
import os
import sys
import logging
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Add the server directory to sys.path if needed
server_dir = os.path.dirname(os.path.abspath(__file__))
if server_dir not in sys.path:
    sys.path.insert(0, server_dir)

# Import the JiraClient class
from app.services.jira import JiraClient

def main():
    # Create a test account ID
    test_account_id = "5ec794101114700c34fe1d9f"  # This is the format for "deencat"
    
    print(f"\n=== Testing Jira account ID validation for format: {test_account_id} ===\n")
    
    # Create a JiraClient instance
    client = JiraClient()
    
    print("Testing client.find_user_account_id with numeric ID format...")
    result = client.find_user_account_id(test_account_id)
    print(f"Result: {result}")
    print(f"Validation passed: {result == test_account_id}")
    
    print("\nTesting basic format validators:")
    
    # Test UUID format validation (should fail for this ID)
    is_uuid = (isinstance(test_account_id, str) and 
               len(test_account_id) > 20 and 
               '-' in test_account_id and 
               test_account_id.count('-') >= 4)
    print(f"UUID format check: {'✓' if is_uuid else '✗'}")
      # Test numeric ID format validation (should pass)
    is_numeric = (isinstance(test_account_id, str) and 
                  len(test_account_id) > 10 and
                  test_account_id.startswith("5") and
                  all(c.isalnum() for c in test_account_id))
    print(f"Numeric format check: {'✓' if is_numeric else '✗'}")
    
    # Test alphanumeric format validation (should pass)
    is_alphanumeric = (isinstance(test_account_id, str) and
                       len(test_account_id) > 10 and
                       all(c.isalnum() for c in test_account_id))
    print(f"Alphanumeric format check: {'✓' if is_alphanumeric else '✗'}")
    
    # Now specifically test looking up deencat
    print("\nLooking up account ID for 'deencat'...")
    deencat_id = client.find_user_account_id("deencat")
    if deencat_id:
        print(f"Found account ID for deencat: {deencat_id}")
    else:
        print("Could not find account ID for deencat")
    
    print("\nAll tests completed!")

if __name__ == "__main__":
    main()
