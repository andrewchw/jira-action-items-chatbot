#!/usr/bin/env python3
"""
This utility script demonstrates how to find a Jira Cloud user's accountId.
This can be useful for testing or debugging assignee issues.

Usage:
  python get_jira_user_id.py <username_or_email>

Example:
  python get_jira_user_id.py deencat

Requirements:
  - Valid Jira credentials in environment variables (JIRA_URL, JIRA_USERNAME, JIRA_API_TOKEN)
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

def main():
    # Check if username was provided
    if len(sys.argv) < 2:
        print("Usage: python get_jira_user_id.py <username_or_email>")
        sys.exit(1)
    
    # Get username from command line
    username_or_email = sys.argv[1]
    
    # Create Jira client
    client = JiraClient()
    
    print(f"Looking up Jira user account ID for: {username_or_email}")
    print(f"Jira instance: {client.base_url}")
    print(f"Is Jira Cloud: {client.is_cloud}")
    
    # Try to find user
    if client.is_cloud:
        # For Cloud instances, search for account ID
        account_id = client.find_user_account_id(username_or_email)
        
        if account_id:
            print(f"\n✓ Success! Found account ID: {account_id}")
            print("\nIn Jira Cloud API calls, use this format:")
            print('{\n  "assignee": {\n    "accountId": "' + account_id + '"\n  }\n}')
        else:
            print(f"\n✗ Error: Could not find account ID for '{username_or_email}'")
            print("Make sure the user exists and your credentials have permission to view users.")
    else:
        # For Server/DC instances, just use the username
        print("\nThis is a Server/DC instance, so you can use the username directly:")
        print('{\n  "assignee": {\n    "name": "' + username_or_email + '"\n  }\n}')
    
    # Try to get myself to verify credentials
    try:
        me = client.get_myself()
        if me and "displayName" in me:
            print(f"\nAuthenticated as: {me.get('displayName')}")
            if client.is_cloud:
                print(f"Your account ID: {me.get('accountId')}")
    except Exception as e:
        print(f"\nError verifying credentials: {str(e)}")
        print("Make sure your JIRA_URL, JIRA_USERNAME, and JIRA_API_TOKEN environment variables are set correctly.")

if __name__ == "__main__":
    main()
