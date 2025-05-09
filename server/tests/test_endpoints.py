import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root_endpoint():
    """
    Test the root endpoint returns the correct status
    """
    response = client.get("/")
    assert response.status_code == 200
    assert "status" in response.json()
    assert response.json()["status"] == "API is running"

def test_health_endpoint():
    """
    Test the health check endpoint returns the correct status
    """
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_get_jira_tasks():
    """
    Test the /jira/tasks endpoint returns sample tasks
    """
    response = client.get("/api/jira/tasks")
    assert response.status_code == 200
    data = response.json()
    assert "tasks" in data
    assert len(data["tasks"]) > 0
    assert "id" in data["tasks"][0]
    assert "title" in data["tasks"][0]
    assert "status" in data["tasks"][0]

def test_chat_endpoint_valid_input():
    """
    Test the chat endpoint with valid input
    """
    response = client.post("/api/chat", json={"text": "Help with tasks"})
    assert response.status_code == 200
    assert "response" in response.json()
    assert response.json()["response"] != ""

def test_chat_endpoint_invalid_input():
    """
    Test the chat endpoint with invalid input (missing text)
    """
    response = client.post("/api/chat", json={})
    assert response.status_code == 400
    assert "detail" in response.json()
    assert "required" in response.json()["detail"].lower() 