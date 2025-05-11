#!/usr/bin/env python3
"""
This script tests assigning an issue to the "deencat" user in Jira Cloud.
It demonstrates the proper way to convert a username to an accountId for Jira Cloud.

Usage:
  python test_deencat_assignee.py
"""

import os
import sys
import logging
import json
from app.services.jira import JiraClient, create_jira_issue
from app.models.database import get_db, get_jira_user_by_name

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_create_issue_with_deencat():
    """
    Test creating an issue with deencat as assignee
    """
    # Create input entities
    entities = {
        "project_key": "JCAI",  # Change to your project key
        "summary": "Test assignee to deencat",
        "description": "Testing the fix for assigning issues to users in Jira Cloud",
        "issue_type": "Task",
        "priority": "Medium",
        "assignee": "deencat"  # This is the problematic assignee
    }
    
    print(f"Attempting to create Jira issue with assignee: {entities['assignee']}")
    print(f"Project key: {entities['project_key']}")
    
    # First, let's check if we have cached the user
    db = next(get_db())
    cached_user = get_jira_user_by_name(db, "deencat")
    if cached_user:
        print(f"Found deencat in cache: {cached_user.display_name}")
        if cached_user.account_id:
            print(f"Cached account ID: {cached_user.account_id}")
    else:
        print("User 'deencat' not found in cache")
    
    # Try to create the issue
    result = create_jira_issue(entities)
    
    print("\nResult:")
    print(json.dumps(result, indent=2))
    
    # Return success or failure
    if result and "success" in result and result["success"]:
        print(f"\n✓ Success! Created issue: {result.get('key')}")
        return True
    else:
        print(f"\n✗ Error: {result.get('error')}")
        if "details" in result:
            print(f"Details: {result.get('details')}")
        return False

def lookup_account_id():
    """
    Utility function to look up the account ID for 'deencat'
    """
    client = JiraClient()
    print("Looking up account ID for 'deencat'...")
    account_id = client.find_user_account_id("deencat")
    
    if account_id:
        print(f"\nFound account ID: {account_id}")
        print("\nFor manual testing, use this JSON:")
        print('{\n  "assignee": {\n    "accountId": "' + account_id + '"\n  }\n}')
    else:
        print("\nCould not find account ID for 'deencat'")

def main():
    print("== Testing Jira Cloud Assignee Fix for 'deencat' ==\n")
    
    # First, let's just look up the account ID
    lookup_account_id()
    
    # Ask if user wants to proceed with creating an issue
    answer = input("\nDo you want to try creating a test issue with deencat as assignee? (y/n): ")
    if answer.lower() == 'y':
        test_create_issue_with_deencat()

if __name__ == "__main__":
    main()
