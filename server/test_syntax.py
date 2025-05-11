"""
Quick test to check if the Jira client class syntax is correct
with focus on assignee and reporter handling
"""
import os
import sys
from pathlib import Path
import json

# Add the current directory to the path so we can import from app
sys.path.insert(0, os.path.abspath('.'))

# Import the necessary modules
try:
    from app.services.jira import JiraClient
    from app.core.config import settings
    print("[OK] Successfully imported JiraClient class and settings")
except Exception as e:
    print(f"[ERROR] Error importing modules: {str(e)}")
    sys.exit(1)

# Store original settings
original_jira_url = settings.JIRA_URL

# Create an instance of the client with cloud URL
try:    # Temporarily modify settings
    settings.JIRA_URL = "https://example.atlassian.net"
    cloud_client = JiraClient()
    print("[OK] Successfully instantiated JiraClient (cloud)")
    print(f"   Is Cloud: {cloud_client.is_cloud}")
except Exception as e:
    print(f"[ERROR] Error instantiating JiraClient (cloud): {str(e)}")
    # Restore original settings
    settings.JIRA_URL = original_jira_url
    sys.exit(1)

# Create an instance of the client with server URL
try:    # Temporarily modify settings
    settings.JIRA_URL = "https://jira.example.com"
    server_client = JiraClient()
    print("[OK] Successfully instantiated JiraClient (server)")
    print(f"   Is Cloud: {server_client.is_cloud}")
except Exception as e:
    print(f"[ERROR] Error instantiating JiraClient (server): {str(e)}")
    # Restore original settings
    settings.JIRA_URL = original_jira_url
    sys.exit(1)

# Restore original settings
settings.JIRA_URL = original_jira_url

# Mock the _map_priority_name and _format_date methods if needed
try:
    # Only add these methods if they don't already exist
    if not hasattr(JiraClient, '_map_priority_name'):
        JiraClient._map_priority_name = lambda self, p: p.capitalize()
    if not hasattr(JiraClient, '_format_date'):
        JiraClient._format_date = lambda self, d: d
    
    print("[OK] Successfully ensured helper methods exist")
except Exception as e:
    print(f"[ERROR] Error adding helper methods: {str(e)}")
    sys.exit(1)

# Test assignee with email (cloud)
try:
    entities = {
        "summary": "Test issue",
        "description": "Test description",
        "assignee": "test.user@example.com",
    }
    
    jira_fields = cloud_client.map_nl_to_jira_fields(entities)    
    print("\n[OK] Successfully mapped assignee with email (cloud)")
    print(f"   Assignee field: {json.dumps(jira_fields.get('assignee', {}), indent=2)}")
except Exception as e:
    print(f"\n[ERROR] Error mapping assignee with email (cloud): {str(e)}")
    sys.exit(1)

# Test assignee with username (cloud)
try:
    entities = {
        "summary": "Test issue",
        "description": "Test description",
        "assignee": "testuser",
    }
    
    jira_fields = cloud_client.map_nl_to_jira_fields(entities)    
    print("\n[OK] Successfully mapped assignee with username (cloud)")
    print(f"   Assignee field: {json.dumps(jira_fields.get('assignee', {}), indent=2)}")
except Exception as e:
    print(f"\n[ERROR] Error mapping assignee with username (cloud): {str(e)}")
    sys.exit(1)

# Test assignee with username (server)
try:
    entities = {
        "summary": "Test issue",
        "description": "Test description",
        "assignee": "testuser",
    }
    
    jira_fields = server_client.map_nl_to_jira_fields(entities)    
    print("\n[OK] Successfully mapped assignee with username (server)")
    print(f"   Assignee field: {json.dumps(jira_fields.get('assignee', {}), indent=2)}")
except Exception as e:
    print(f"\n[ERROR] Error mapping assignee with username (server): {str(e)}")
    sys.exit(1)

# Test reporter with email
try:
    entities = {
        "summary": "Test issue",
        "description": "Test description",
        "reporter": "test.reporter@example.com",
    }
    
    jira_fields = cloud_client.map_nl_to_jira_fields(entities)    
    print("\n[OK] Successfully mapped reporter with email")
    print(f"   Reporter field: {json.dumps(jira_fields.get('reporter', {}), indent=2)}")
except Exception as e:
    print(f"\n[ERROR] Error mapping reporter with email: {str(e)}")
    sys.exit(1)

print("\n[OK] All syntax tests passed!")
sys.exit(0)
