#!/usr/bin/env python3
"""
Follow-up Sender for CLAVE.AI v2.0
Sistema de follow-up en ESCALERA:
- Día 1: Primer follow-up casual
- Día 2: Enviar lead magnet gratis
- Día 5: Último follow-up antes de cerrar
Runs via GitHub Actions schedule.
"""

import asyncio
import os
import json
import httpx
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# Import the tracker from daily_scraper
import sys
sys.path.insert(0, os.path.dirname(__file__))
from daily_scraper import LeadTracker

# Mensajes de follow-up por etapa
FOLLOWUP_MESSAGES = {
    "day_1": """Hola! 👋 Te escribí ayer, ¿pudiste verlo?

Si no tienes tiempo ahorita no hay problema, solo quería saber si te llegó bien el mensaje.

Cualquier cosa me dices 👍""",
    
    "day_2": """Hola! Pasando a dejarte algo gratis 🎁

{leadmagnet}

Es tuyo, sin compromiso. También puedes ver nuestras soluciones en vivo aquí: https://claveai-demo.ckoomq.easypanel.host/

Si después quieres platicar sobre cómo automatizarlo, aquí andamos.

Saludos!""",
    
    "day_5": """Hola! Último mensaje, lo prometo 😅

Solo quería cerrar el círculo: ¿te sirvió lo que te mandé sobre {nombre}?

Si no es buen momento, sin problema. Guardamos tu contacto por si más adelante necesitas algo.

Suerte! 🙌"""
}


async def send_followups_to_n8n():
    """
    Busca leads según su antigüedad y envía el follow-up correspondiente:
    - Día 1: Primer recordatorio
    - Día 2: Envío de lead magnet
    - Día 5: Cierre y despedida
    """
    raw_url = os.getenv("N8N_WEBHOOK_URL", "")
    webhook_url = raw_url.strip().replace("\n", "").replace("\r", "") if raw_url else None
    
    if not webhook_url:
        print("[ERROR] No N8N_WEBHOOK_URL configured")
        return
    
    tracker = LeadTracker()
    
    # =========================================================================
    # FOLLOW-UP DÍA 1 - Leads contactados ayer
    # =========================================================================
    leads_day_1 = tracker.get_leads_for_followup(days_since_contact=1)
    leads_day_1 = [l for l in leads_day_1 if not l.get("followup_day1_sent", False)]
    
    # =========================================================================
    # FOLLOW-UP DÍA 2 - Leads contactados hace 2 días (enviar lead magnet)
    # =========================================================================
    leads_day_2 = tracker.get_leads_for_followup(days_since_contact=2)
    leads_day_2 = [l for l in leads_day_2 if not l.get("followup_day2_sent", False)]
    
    # =========================================================================
    # FOLLOW-UP DÍA 5 - Cierre final
    # =========================================================================
    leads_day_5 = tracker.get_leads_for_followup(days_since_contact=5)
    leads_day_5 = [l for l in leads_day_5 if not l.get("followup_sent", False)]
    
    print(f"\n📊 RESUMEN DE FOLLOW-UPS:")
    print(f"   Día 1 (recordatorio): {len(leads_day_1)} leads")
    print(f"   Día 2 (lead magnet): {len(leads_day_2)} leads")
    print(f"   Día 5 (cierre): {len(leads_day_5)} leads")
    
    all_followups = []
    
    # Preparar follow-ups día 1
    for lead in leads_day_1:
        all_followups.append({
            "phone": lead["phone"],
            "message": FOLLOWUP_MESSAGES["day_1"],
            "lead_name": lead.get("lead_name", ""),
            "followup_type": "day_1",
            "days_since_contact": 1
        })
    
    # Preparar follow-ups día 2 (con lead magnet)
    for lead in leads_day_2:
        leadmagnet = lead.get("leadmagnet", "un recurso gratis que te puede servir")
        message = FOLLOWUP_MESSAGES["day_2"].format(leadmagnet=leadmagnet)
        all_followups.append({
            "phone": lead["phone"],
            "message": message,
            "lead_name": lead.get("lead_name", ""),
            "followup_type": "day_2",
            "days_since_contact": 2
        })
    
    # Preparar follow-ups día 5 (cierre)
    for lead in leads_day_5:
        message = FOLLOWUP_MESSAGES["day_5"].format(nombre=lead.get("lead_name", "tu negocio"))
        all_followups.append({
            "phone": lead["phone"],
            "message": message,
            "lead_name": lead.get("lead_name", ""),
            "followup_type": "day_5",
            "days_since_contact": 5
        })
    
    if not all_followups:
        print("[INFO] No hay leads pendientes de follow-up")
        stats = tracker.get_stats()
        print(f"[STATS] Total contactados: {stats['total_contacted']} | Pendientes: {stats['pending_followups']}")
        return
    
    print(f"\n[FOLLOWUP] Enviando {len(all_followups)} follow-ups en total...")
    
    for followup in all_followups:
        print(f"  - {followup['lead_name']} ({followup['phone']}) - Tipo: {followup['followup_type']}")
    
    try:
        async with httpx.AsyncClient() as client:
            payload = {
                "leads": all_followups,
                "total_count": len(all_followups),
                "source": "followup_sender_v2",
                "is_followup": True,
                "timestamp": datetime.now().isoformat()
            }
            
            response = await client.post(webhook_url, json=payload, timeout=60.0)
            print(f"[N8N] Enviados {len(all_followups)} follow-ups | Status: {response.status_code}")
            
            if response.status_code == 200:
                # Marcar día 5 como enviados (cierre definitivo)
                phones_day_5 = [lead["phone"] for lead in leads_day_5]
                if phones_day_5:
                    tracker.mark_followup_sent(phones_day_5)
                    print(f"[TRACKER] Marcados {len(phones_day_5)} leads como CERRADOS (follow-up final)")
                
    except Exception as e:
        print(f"[ERROR] Failed to send follow-ups: {type(e).__name__}: {e}")


async def main():
    print(f"\n📨 CLAVE.AI Follow-up Sender v2.0")
    print(f"{'='*60}")
    print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"📡 Webhook: {os.getenv('N8N_WEBHOOK_URL', 'NOT SET')[:50]}...")
    print(f"{'='*60}")
    
    await send_followups_to_n8n()
    
    print(f"\n{'='*60}")
    print(f"✅ Follow-up sender completado")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(main())

