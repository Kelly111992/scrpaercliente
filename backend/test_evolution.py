#!/usr/bin/env python3
"""Test sending WhatsApp message via Evolution API"""
import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

async def test_evolution_api():
    evolution_url = os.getenv("EVOLUTION_API_URL", "")
    evolution_key = os.getenv("EVOLUTION_API_KEY", "")
    evolution_instance = os.getenv("EVOLUTION_INSTANCE_NAME", "claveai")
    
    print(f"EVOLUTION_API_URL: {evolution_url}")
    print(f"EVOLUTION_API_KEY: {evolution_key[:10]}..." if evolution_key else "EVOLUTION_API_KEY: (not set)")
    print(f"EVOLUTION_INSTANCE_NAME: {evolution_instance}")
    
    if not evolution_key:
        print("ERROR: No EVOLUTION_API_KEY configured!")
        return
    
    # Número de prueba (admin)
    phone = "523318213624"
    message = "🔧 Mensaje de prueba desde el scraper CLAVE.AI - Evolution API directa"
    
    url = f"{evolution_url}/message/sendText/{evolution_instance}"
    headers = {
        "apikey": evolution_key,
        "Content-Type": "application/json"
    }
    # Formato correcto para Evolution API v2
    payload = {
        "number": phone,
        "text": message
    }
    
    print(f"\nURL: {url}")
    print(f"Headers: {headers}")
    print(f"Payload: {payload}\n")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=30.0)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
            
            if response.status_code in [200, 201]:
                print("\n✅ Mensaje enviado exitosamente!")
            else:
                print(f"\n❌ Error: {response.status_code}")
    except Exception as e:
        print(f"Exception: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(test_evolution_api())
