#!/usr/bin/env python3
"""
Debug script for testing the specific issue with "deencat" account ID.
"""
import os
import sys
import logging
import json
import traceback
from app.services.jira import JiraClient

# Set up verbose logging to console
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG for most detailed output
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

def main():
    """Test with the deencat user specifically"""
    print("\n=== Testing account ID handling for 'deencat' ===\n")
    
    # Create Jira client
    client = JiraClient()
    print(f"Jira URL: {client.base_url}")
    print(f"Is Cloud: {client.is_cloud}")
    
    # Test direct account ID handling
    account_id = "5ec794101114700c34fe1d9f"  # Known format for deencat
    print(f"\nTesting direct account ID validation for: {account_id}")
    
    # Check if our validation would accept this ID format
    is_standard_uuid = (len(account_id) > 20 and '-' in account_id and account_id.count('-') >= 4)
    is_numeric_format = (len(account_id) > 10 and account_id.startswith("5") and all(c.isalnum() for c in account_id))
    is_alphanumeric = (len(account_id) > 10 and all(c.isalnum() for c in account_id))
    
    print(f"UUID format check: {is_standard_uuid}")
    print(f"Numeric format check: {is_numeric_format}")
    print(f"Alphanumeric format check: {is_alphanumeric}")
    
    # Test the find_user_account_id method with direct ID
    print("\nTesting find_user_account_id with direct account ID...")
    result = client.find_user_account_id(account_id)
    print(f"Result: {result}")
    print(f"Same as input: {result == account_id}")
    
    # Now test with username "deencat"
    print("\nTesting find_user_account_id with username 'deencat'...")
    username_result = client.find_user_account_id("deencat")
    print(f"Result: {username_result}")
    if username_result:
        print(f"Found account ID: {username_result}")
    else:
        print("Failed to find account ID")

    # Try creating a test issue
    print("\nCreating test issue with deencat as assignee...")
    test_data = {
        "project_key": "JCAI",  # Adjust to your project
        "summary": "Testing deencat assignee",
        "description": "This is a test issue for deencat assignee handling",
        "assignee": "deencat"  # Try with username first
    }
    
    try:
        # This uses the create_jira_issue function that contains our fixes
        from app.services.jira import create_jira_issue
        result = create_jira_issue(test_data)
        print("\nResult:")
        print(json.dumps(result, indent=2))
        if result.get("success"):
            print(f"\nSuccess! Created issue {result.get('key')}")
        else:
            print(f"\nFailed: {result.get('error')}")
            
            # Try again with direct account ID
            print("\nRetrying with direct account ID...")
            test_data["assignee"] = account_id
            result = create_jira_issue(test_data)
            print("Result:")
            print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"EXCEPTION: {str(e)}")
        print(traceback.format_exc())
        sys.exit(1)
