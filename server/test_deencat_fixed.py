#!/usr/bin/env python3
"""
Test creating an issue with the deencat assignee.
"""
import sys
import logging
import json
from app.services.jira import create_jira_issue

# Configure logging
logging.basicConfig(level=logging.INFO)

def main():
    # Create test issue data with deencat as assignee
    issue_data = {
        "project_key": "JCAI",  # Change to your project if needed
        "summary": "Test issue for deencat assignee",
        "description": "This is a test to verify the fix for deencat account ID handling",
        "issue_type": "Task",
        "assignee": "deencat"
    }
    
    print(f"\n=== Testing issue creation with assignee: {issue_data['assignee']} ===\n")
    
    # Try creating the issue
    result = create_jira_issue(issue_data)
    
    # Print the result
    print("Result:")
    print(json.dumps(result, indent=2))
    
    # Check if it was successful
    if "success" in result and result["success"]:
        print(f"\n✓ SUCCESS! Issue created: {result.get('key')}")
        print(f"Assignee was set to: {result.get('assignee')}")
    else:
        print(f"\n✗ FAILED: {result.get('error')}")
        if "details" in result:
            print(f"Details: {result.get('details')}")
    
    # Now try with direct account ID
    print("\n=== Testing issue creation with direct account ID ===\n")
    
    # Update issue data with direct account ID
    issue_data["assignee"] = "5ec794101114700c34fe1d9f"  # deencat's account ID
    issue_data["summary"] = "Test issue with direct account ID"
    
    # Try creating the issue
    result = create_jira_issue(issue_data)
    
    # Print the result
    print("Result:")
    print(json.dumps(result, indent=2))
    
    # Check if it was successful
    if "success" in result and result["success"]:
        print(f"\n✓ SUCCESS! Issue created: {result.get('key')}")
        print(f"Assignee was set to: {result.get('assignee')}")
    else:
        print(f"\n✗ FAILED: {result.get('error')}")
        if "details" in result:
            print(f"Details: {result.get('details')}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
