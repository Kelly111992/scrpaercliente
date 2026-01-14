import requests
import json

payload = {
    "leads": [
        {
            "phone": "5213312345678",
            "message": "Qué tal! Vi tu veterinaria Clínica Test en Google Maps.\nHago sistemas de recordatorios automáticos de citas y vacunas para veterinarias.\n¿Actualmente cómo le haces para recordarle a tus clientes sus citas? 🐾",
            "followup_message": "Hola de nuevo! Te escribí hace unos días sobre automatizar recordatorios.\n¿Te gustaría que te muestre cómo funciona en 5 min? Sin compromiso 👍",
            "lead_name": "Clínica Test",
            "category": "veterinaria",
            "nicho": "veterinaria",
            "website": "",
            "google_maps_url": "https://maps.google.com/test"
        }
    ],
    "total_count": 1,
    "source": "test_scraper",
    "is_followup": False,
    "timestamp": "2026-01-14T16:09:00"
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
