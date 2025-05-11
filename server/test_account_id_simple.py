#!/usr/bin/env python3
"""
Simple script to verify that our non-standard account ID handling works.
"""
import sys
import logging
from app.services.jira import JiraClient

# Configure logging
logging.basicConfig(level=logging.INFO)

def main():
    # Create a Jira client
    client = JiraClient()
    
    # The account ID for "deencat" in the non-UUID format
    account_id = "5ec794101114700c34fe1d9f"
    
    # Test if our code recognizes it as a valid account ID
    result = client.find_user_account_id(account_id)
    
    print(f"\nTesting account ID validation for: {account_id}")
    print(f"Result: {result}")
    print(f"Success: {result == account_id}")
    
    # Also verify that we can lookup deencat by username
    username_result = client.find_user_account_id("deencat")
    print(f"\nLooking up 'deencat' by username:")
    print(f"Result: {username_result}")
    
    # Test if this ID format is recognized in validation
    # Case 1: Standard UUID format with dashes (should fail)
    is_uuid = (isinstance(account_id, str) and 
              len(account_id) > 20 and 
              '-' in account_id and 
              account_id.count('-') >= 4)
              
    # Case 2: Atlassian numeric format (should pass)
    is_numeric = (isinstance(account_id, str) and 
                 len(account_id) > 10 and
                 account_id.startswith("5") and
                 all(c.isalnum() for c in account_id))
                 
    # Case 3: Alphanumeric format (should pass)
    is_alphanumeric = (isinstance(account_id, str) and
                      len(account_id) > 10 and
                      all(c.isalnum() for c in account_id))
                      
    print("\nFormat validation results:")
    print(f"UUID format check: {'✓' if is_uuid else '✗'}")
    print(f"Numeric format check: {'✓' if is_numeric else '✗'}")
    print(f"Alphanumeric format check: {'✓' if is_alphanumeric else '✗'}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
