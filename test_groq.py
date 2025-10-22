#!/usr/bin/env python3
"""
Test script for Groq AI integration
"""
import asyncio
import httpx
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_groq_chat():
    """Test the Groq chat endpoint"""
    base_url = "http://localhost:8000"  # Adjust if running on different port

    # Test payload for Groq
    payload = {
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello! Can you tell me about yourself?"}
        ],
        "model": "llama-3.1-70b-versatile",
        "temperature": 0.7,
        "max_tokens": 1024
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{base_url}/ai/chat", json=payload)
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Testing Groq integration...")
    asyncio.run(test_groq_chat())