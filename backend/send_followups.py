#!/usr/bin/env python3
"""
Follow-up Sender for CLAVE.AI
Envía mensajes de seguimiento a leads contactados hace 3 días.
Runs via GitHub Actions schedule.
"""

import asyncio
import os
import json
import httpx
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Import the tracker from daily_scraper
import sys
sys.path.insert(0, os.path.dirname(__file__))
from daily_scraper import LeadTracker


async def send_followups_to_n8n():
    """
    Busca leads que fueron contactados hace 3+ días y envía follow-up a n8n
    """
    raw_url = os.getenv("N8N_WEBHOOK_URL", "")
    webhook_url = raw_url.strip().replace("\n", "").replace("\r", "") if raw_url else None
    
    if not webhook_url:
        print("[ERROR] No N8N_WEBHOOK_URL configured")
        return
    
    tracker = LeadTracker()
    
    # Obtener leads que necesitan follow-up (3 días desde contacto)
    leads_to_followup = tracker.get_leads_for_followup(days_since_contact=3)
    
    if not leads_to_followup:
        print("[INFO] No hay leads pendientes de follow-up")
        stats = tracker.get_stats()
        print(f"[STATS] Total contactados: {stats['total_contacted']} | Pendientes: {stats['pending_followups']}")
        return
    
    print(f"[FOLLOWUP] Encontrados {len(leads_to_followup)} leads para follow-up")
    
    for lead in leads_to_followup:
        print(f"  - {lead['lead_name']} ({lead['phone']}) - {lead['days_since_contact']} días")
    
    try:
        async with httpx.AsyncClient() as client:
            payload = {
                "leads": leads_to_followup,
                "total_count": len(leads_to_followup),
                "source": "followup_sender",
                "is_followup": True,  # Flag para que n8n sepa que es follow-up
                "timestamp": datetime.now().isoformat()
            }
            
            response = await client.post(webhook_url, json=payload, timeout=60.0)
            print(f"[N8N] Enviados {len(leads_to_followup)} follow-ups | Status: {response.status_code}")
            
            if response.status_code == 200:
                # Marcar como enviados
                phones = [lead["phone"] for lead in leads_to_followup]
                tracker.mark_followup_sent(phones)
                print(f"[TRACKER] Marcados {len(phones)} follow-ups como enviados")
            
    except Exception as e:
        print(f"[ERROR] Failed to send follow-ups: {type(e).__name__}: {e}")


async def main():
    print(f"\n📨 CLAVE.AI Follow-up Sender")
    print(f"{'='*60}")
    print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"📡 Webhook: {os.getenv('N8N_WEBHOOK_URL', 'NOT SET')[:50]}...")
    print(f"{'='*60}\n")
    
    await send_followups_to_n8n()
    
    print(f"\n{'='*60}")
    print(f"✅ Follow-up sender completado")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(main())
