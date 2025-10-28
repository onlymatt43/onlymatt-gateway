#!/usr/bin/env python3
import os
import asyncio
from gateway import app
from fastapi.testclient import TestClient

# Set test environment variables
os.environ["GROQ_API_KEY"] = "test-key"  # This will fail but should not crash

# Create test client
client = TestClient(app)

def test_health():
    """Test health endpoint"""
    response = client.get("/health")
    print(f"Health: {response.status_code} - {response.json()}")

def test_ai_health():
    """Test AI health endpoint"""
    response = client.get("/ai/health")
    print(f"AI Health: {response.status_code} - {response.json()}")

def test_chat():
    """Test chat endpoint"""
    payload = {
        "messages": [{"role": "user", "content": "Hello"}],
        "model": "test",
        "temperature": 0.7,
        "max_tokens": 100
    }
    response = client.post("/ai/chat", json=payload)
    print(f"Chat: {response.status_code} - {response.text[:200]}")

if __name__ == "__main__":
    print("Testing OnlyMatt Gateway locally...")
    test_health()
    test_ai_health()
    test_chat()
    print("Tests completed.")