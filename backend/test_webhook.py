#!/usr/bin/env python3
"""Test webhook connection to n8n"""
import httpx
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def test_webhook():
    webhook_url = os.getenv("N8N_WEBHOOK_URL", "")
    print(f"Testing webhook: {webhook_url}")
    
    if not webhook_url:
        print("ERROR: N8N_WEBHOOK_URL not set")
        return
    
    try:
        async with httpx.AsyncClient() as client:
            payload = {
                "leads": [
                    {
                        "phone": "523312345678",
                        "message": "Test message from debug script",
                        "lead_name": "Test Lead",
                        "category": "Test",
                        "website": "",
                        "google_maps_url": ""
                    }
                ],
                "total_count": 1,
                "source": "test_script",
                "timestamp": "2026-01-04T13:30:00"
            }
            response = await client.post(webhook_url, json=payload, timeout=30.0)
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text[:500]}")
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(test_webhook())
