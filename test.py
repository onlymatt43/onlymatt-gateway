#!/usr/bin/env python3
"""
Test script for ONLYMATT Gateway
"""
import os
import sys
import asyncio
import httpx
from dotenv import load_dotenv

load_dotenv()

async def test_health():
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get("http://localhost:8000/health")
            print(f"Health: {r.status_code} - {r.json()}")
        except Exception as e:
            print(f"Health failed: {e}")

async def test_turso():
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get("http://localhost:8000/ai/tursocheck")
            print(f"Turso check: {r.status_code} - {r.json()}")
        except Exception as e:
            print(f"Turso check failed: {e}")

async def test_lib():
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get("http://localhost:8000/ai/libcheck")
            print(f"Lib check: {r.status_code} - {r.json()}")
        except Exception as e:
            print(f"Lib check failed: {e}")

async def main():
    print("Testing ONLYMATT Gateway...")
    await test_health()
    await test_lib()
    await test_turso()

if __name__ == "__main__":
    asyncio.run(main())