"""
Debug script for OAuth integration with Atlassian.
Run this script to verify your OAuth configuration and troubleshoot issues.
"""

import os
import sys
import requests
import json
from urllib.parse import urlencode
from app.core.config import settings

def print_header(title):
    """Print a formatted header for better readability"""
    print("\n" + "=" * 70)
    print(f" {title} ".center(70, "="))
    print("=" * 70 + "\n")

def print_section(title):
    """Print a section title"""
    print("\n" + "-" * 50)
    print(f" {title} ".center(50, "-"))
    print("-" * 50)

def print_kvp(key, value):
    """Print a key-value pair with formatting"""
    # Mask secrets in output
    if any(secret_key in key.lower() for secret_key in ['secret', 'token', 'password', 'key']):
        # Show just the beginning and end if it's a long string
        if isinstance(value, str) and len(value) > 10:
            display_value = f"{value[:5]}...{value[-5:]}" if value else "Not set"
        else:
            display_value = "********" if value else "Not set"
    else:
        display_value = value if value else "Not set"
    
    print(f"{key.ljust(30)}: {display_value}")

def test_atlassian_api():
    """Test making a simple request to the Atlassian API"""
    print_section("Testing Atlassian API Connectivity")
    
    url = "https://api.atlassian.com/oauth/token/accessible-resources"
    headers = {
        "Accept": "application/json"
    }
    
    try:
        print(f"Making HEAD request to Atlassian API...")
        response = requests.head("https://auth.atlassian.com")
        print(f"Response status code: {response.status_code}")
        print(f"Response headers: {json.dumps(dict(response.headers), indent=2)}")
        
        return True
    except Exception as e:
        print(f"Error connecting to Atlassian API: {str(e)}")
        return False

def generate_auth_url():
    """Generate an OAuth authorization URL for testing"""
    print_section("OAuth Authorization URL")
    
    # OAuth 2.0 settings
    oauth_authorization_url = "https://auth.atlassian.com/authorize"
    oauth_scope = "read:jira-user read:jira-work write:jira-work"
    
    # Build the authorization URL (similar to the login endpoint)
    params = {
        "audience": "api.atlassian.com",
        "client_id": settings.JIRA_OAUTH_CLIENT_ID,
        "scope": oauth_scope,
        "redirect_uri": f"{settings.SITE_URL}/api/auth/callback",
        "state": "debug-test-state",
        "response_type": "code",
        "prompt": "consent"
    }
    
    auth_url = f"{oauth_authorization_url}?{urlencode(params)}"
    print(f"Authorization URL: {auth_url}")
    
    return auth_url

def simulate_token_exchange(code=None):
    """Simulate exchanging a code for tokens"""
    if not code:
        print("No authorization code provided. Skipping token exchange simulation.")
        return
        
    print_section("Simulating Token Exchange")
    
    url = "https://auth.atlassian.com/oauth/token"
    data = {
        "grant_type": "authorization_code",
        "client_id": settings.JIRA_OAUTH_CLIENT_ID,
        "client_secret": settings.JIRA_OAUTH_CLIENT_SECRET,
        "code": code,
        "redirect_uri": f"{settings.SITE_URL}/api/auth/callback"
    }
    
    print("Token exchange request data:")
    for key, value in data.items():
        print_kvp(key, value)
    
    try:
        print("\nMaking token exchange request...")
        response = requests.post(url, data=data)
        print(f"Response status code: {response.status_code}")
        
        if response.status_code == 200:
            print("Token exchange successful!")
            token_data = response.json()
            print("Token response data:")
            for key, value in token_data.items():
                print_kvp(key, value)
                
            # Test user info
            if "access_token" in token_data:
                test_user_info(token_data["access_token"])
        else:
            print(f"Token exchange failed. Response: {response.text}")
    except Exception as e:
        print(f"Error during token exchange: {str(e)}")

def test_user_info(access_token):
    """Test getting user info with an access token"""
    print_section("Testing User Info Endpoint")
    
    url = "https://api.atlassian.com/me"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    try:
        print("Making user info request...")
        response = requests.get(url, headers=headers)
        print(f"Response status code: {response.status_code}")
        
        if response.status_code == 200:
            print("User info request successful!")
            print(f"User info: {json.dumps(response.json(), indent=2)}")
        else:
            print(f"User info request failed. Response: {response.text}")
    except Exception as e:
        print(f"Error getting user info: {str(e)}")

def main():
    print_header("Atlassian OAuth Debug Tool")
    
    # Print environment settings
    print_section("Environment Settings")
    print_kvp("JIRA_OAUTH_CLIENT_ID", settings.JIRA_OAUTH_CLIENT_ID)
    print_kvp("JIRA_OAUTH_CLIENT_SECRET", settings.JIRA_OAUTH_CLIENT_SECRET)
    print_kvp("SITE_URL", settings.SITE_URL)
    
    # Test Atlassian API
    test_atlassian_api()
    
    # Generate authorization URL
    auth_url = generate_auth_url()
    
    # Check if an authorization code was provided
    code = None
    if len(sys.argv) > 1:
        code = sys.argv[1]
        print_kvp("Authorization Code", code)
        simulate_token_exchange(code)
    else:
        print("\nNo authorization code provided. To test token exchange, run:")
        print(f"python debug_oauth.py YOUR_AUTH_CODE")
        print("\nYou can get an authorization code by:")
        print("1. Visit the authorization URL above")
        print("2. Complete the authorization flow")
        print("3. Extract the 'code' parameter from the callback URL")

if __name__ == "__main__":
    main() 