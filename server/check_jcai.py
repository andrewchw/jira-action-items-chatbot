"""
Script to check if the JCAI project is accessible
"""
import os
import sys
from dotenv import load_dotenv
from pathlib import Path

# Add the current directory to the path so we can import from app
sys.path.insert(0, os.path.abspath('.'))

# Load environment variables
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

# Now import the JiraClient
from app.services.jira import JiraClient

def main():
    """Check if the JCAI project is accessible"""
    print("Checking JCAI project...")
    
    # Create the client
    client = JiraClient()
    
    # Try to access the JCAI project
    try:
        project = client.get_project('JCAI')
        print(f"✅ JCAI project found: {project.get('name', 'Unknown')}")
        print(f"Project ID: {project.get('id')}")
        print(f"Project key: {project.get('key')}")
        print(f"Project lead: {project.get('lead', {}).get('displayName', 'Unknown')}")
        
        # Get issue types for this project
        try:
            issue_types = [issue_type.get('name') for issue_type in project.get('issueTypes', [])]
            print(f"Available issue types: {', '.join(issue_types)}")
        except Exception:
            print("Could not retrieve issue types")
        
        return 0
    except Exception as e:
        print(f"❌ Error accessing JCAI project: {str(e)}")
        
        # Check if project exists in list of all projects
        try:
            print("\nChecking available projects...")
            projects = client.get_projects()
            project_keys = [p.get('key') for p in projects]
            if 'JCAI' in project_keys:
                print("🤔 JCAI project exists but could not be accessed directly. This might be a permissions issue.")
            else:
                print("🔍 JCAI project not found. Available project keys:")
                for i, key in enumerate(project_keys[:10]):  # Show first 10 project keys
                    print(f"  - {key}")
                if len(project_keys) > 10:
                    print(f"  ... and {len(project_keys) - 10} more")
        except Exception as inner_e:
            print(f"Could not retrieve project list: {str(inner_e)}")
        
        return 1

if __name__ == "__main__":
    sys.exit(main()) 