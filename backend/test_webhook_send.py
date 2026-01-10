import requests
import json

payload = {
    "leads": [
        {
            "phone": "5213312345678",
            "message": "PRUEBA desde scraper - Hola! Este es un mensaje de prueba para verificar los campos.",
            "lead_name": "Negocio de Prueba",
            "category": "veterinaria",
            "website": "https://ejemplo.com",
            "google_maps_url": "https://maps.google.com/test"
        }
    ],
    "total_count": 1,
    "source": "test_scraper",
    "timestamp": "2026-01-10T15:51:00"
}

url = "https://evolutionapi-n8n.ckoomq.easypanel.host/webhook/claveai"

print("Enviando datos de prueba a n8n...")
print(f"URL: {url}")
print(f"Payload: {json.dumps(payload, indent=2)}")

try:
    response = requests.post(url, json=payload, timeout=30)
    print(f"\nStatus: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
