#!/usr/bin/env python3
"""
Test script to verify that our account ID validation logic handles different formats correctly.
"""
import os
import sys
import logging
from app.services.jira import JiraClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_account_id_formats():
    """
    Test that our account ID validation logic handles different formats correctly.
    """
    # Create a Jira client
    client = JiraClient()
    
    # Define test account IDs in different formats
    test_ids = [
        # Standard UUID format
        "12345678-1234-1234-1234-123456789012",
        # Atlassian numeric format 
        "5ec794101114700c34fe1d9f", 
        # Short format (should not be recognized)
        "12345",
        # Another non-standard format
        "5ec794101114700c34fe1d9f123",
        # Email address (should not be recognized as account ID)
        "user@example.com",
        # Username (should not be recognized as account ID)
        "username",
        # Known user "deencat" (if available in your Jira instance)
        "deencat"
    ]
    
    print("\n=== Testing account ID format validation ===\n")
    
    # Test each ID with the find_user_account_id method
    for test_id in test_ids:
        print(f"\nTesting: '{test_id}'")
        
        # Call the method that contains our validation logic
        result = client.find_user_account_id(test_id)
        
        if result == test_id:
            print(f"✅ Recognized as valid account ID: {result}")
        elif result:
            print(f"🔍 Not recognized as account ID but found matching user: {result}")
        else:
            print(f"❌ Not recognized as account ID and no matching user found")
    
    print("\n--- Direct format checking tests ---\n")
    
    # Now just test the format validation logic directly
    for test_id in test_ids:
        # Standard UUID format
        is_uuid = (isinstance(test_id, str) and 
                  len(test_id) > 20 and 
                  '-' in test_id and 
                  test_id.count('-') >= 4)
        
        # Numeric ID format 
        is_numeric = (isinstance(test_id, str) and 
                     len(test_id) > 10 and
                     test_id.startswith("5") and
                     all(c.isdigit() for c in test_id))
        
        # Alphanumeric format
        is_alphanumeric = (isinstance(test_id, str) and
                          len(test_id) > 10 and
                          all(c.isalnum() for c in test_id))
        
        print(f"ID: {test_id}")
        print(f"  - UUID format:       {'✓' if is_uuid else '✗'}")
        print(f"  - Numeric format:    {'✓' if is_numeric else '✗'}")
        print(f"  - Alphanumeric:      {'✓' if is_alphanumeric else '✗'}")
        print()

if __name__ == "__main__":
    test_account_id_formats()
