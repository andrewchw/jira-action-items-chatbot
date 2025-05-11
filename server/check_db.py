#!/usr/bin/env python
import sqlite3
import json

def main():
    print("Connecting to database...")
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    
    # Count users
    cursor.execute('SELECT COUNT(*) FROM jira_user_cache')
    count = cursor.fetchone()[0]
    print(f"Total cached users: {count}")
    
    # Sample users
    cursor.execute('SELECT id, username, email, display_name, active FROM jira_user_cache LIMIT 5')
    print("\nSample users:")
    for row in cursor.fetchall():
        print(f"ID: {row[0]}, Username: {row[1]}, Email: {row[2]}, Name: {row[3]}, Active: {row[4]}")
    
    # Check for duplicates
    cursor.execute('''
        SELECT username, COUNT(*) as count 
        FROM jira_user_cache 
        GROUP BY username 
        HAVING count > 1
    ''')
    duplicates = cursor.fetchall()
    if duplicates:
        print("\nFound duplicate usernames:")
        for dup in duplicates:
            print(f"Username: {dup[0]}, Count: {dup[1]}")
    else:
        print("\nNo duplicate usernames found.")
    
    # Check inactive users
    cursor.execute('SELECT COUNT(*) FROM jira_user_cache WHERE active = 0')
    inactive = cursor.fetchone()[0]
    print(f"\nInactive users: {inactive}")
    
    conn.close()
    print("Database connection closed.")

if __name__ == "__main__":
    main() 