#!/usr/bin/env python3
"""
Follow-up Sender for CLAVE.AI v2.1
Sistema de follow-up en ESCALERA usando Evolution API directamente:
- Día 1: Primer follow-up casual
- Día 2: Enviar lead magnet gratis
- Día 5: Último follow-up antes de cerrar
Runs via GitHub Actions schedule.
"""

import asyncio
import os
import json
import httpx
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# Import the tracker from daily_scraper
import sys
sys.path.insert(0, os.path.dirname(__file__))
from daily_scraper import LeadTracker

# Evolution API Config
EVOLUTION_URL = os.getenv("EVOLUTION_API_URL", "https://evolutionapi-evolution-api.ckoomq.easypanel.host")
EVOLUTION_KEY = os.getenv("EVOLUTION_API_KEY", "")
EVOLUTION_INSTANCE = os.getenv("EVOLUTION_INSTANCE_NAME", "claveai")

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


async def send_whatsapp_message(phone: str, message: str) -> bool:
    """Envía un mensaje de WhatsApp usando Evolution API directamente"""
    if not EVOLUTION_KEY:
        print(f"[ERROR] No EVOLUTION_API_KEY configured")
        return False
    
    try:
        url = f"{EVOLUTION_URL}/message/sendText/{EVOLUTION_INSTANCE}"
        headers = {
            "apikey": EVOLUTION_KEY,
            "Content-Type": "application/json"
        }
        # Formato correcto para Evolution API v2
        payload = {
            "number": phone,
            "text": message
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=30.0)
            
            if response.status_code in [200, 201]:
                print(f"[EVOLUTION] ✅ Follow-up enviado a {phone}")
                return True
            else:
                print(f"[EVOLUTION] ❌ Error enviando a {phone}: {response.status_code} - {response.text[:200]}")
                return False
    except Exception as e:
        print(f"[EVOLUTION] Exception enviando a {phone}: {e}")
        return False


async def send_followups_via_evolution():
    """
    Busca leads según su antigüedad y envía el follow-up correspondiente
    directamente via Evolution API (sin n8n):
    - Día 1: Primer recordatorio
    - Día 2: Envío de lead magnet
    - Día 5: Cierre y despedida
    """
    if not EVOLUTION_KEY:
        print("[ERROR] No EVOLUTION_API_KEY configured - no se pueden enviar follow-ups")
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
    
    print(f"\n[FOLLOWUP] Enviando {len(all_followups)} follow-ups via Evolution API...")
    
    sent_count = 0
    for followup in all_followups:
        print(f"  📤 {followup['lead_name']} ({followup['phone']}) - Tipo: {followup['followup_type']}")
        
        success = await send_whatsapp_message(followup["phone"], followup["message"])
        if success:
            sent_count += 1
        
        # Delay entre mensajes para evitar rate limiting
        await asyncio.sleep(random.randint(2000, 4000) / 1000)
    
    # Marcar día 5 como enviados (cierre definitivo)
    phones_day_5 = [lead["phone"] for lead in leads_day_5]
    if phones_day_5:
        tracker.mark_followup_sent(phones_day_5)
        print(f"[TRACKER] Marcados {len(phones_day_5)} leads como CERRADOS (follow-up final)")
    
    print(f"\n[EVOLUTION] ✅ Enviados {sent_count}/{len(all_followups)} follow-ups exitosamente")


async def main():
    print(f"\n📨 CLAVE.AI Follow-up Sender v2.1 (Evolution API Directa)")
    print(f"{'='*60}")
    print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"🔗 Evolution: {EVOLUTION_URL[:50]}...")
    print(f"📱 Instancia: {EVOLUTION_INSTANCE}")
    print(f"{'='*60}")
    
    await send_followups_via_evolution()
    
    print(f"\n{'='*60}")
    print(f"✅ Follow-up sender completado")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(main())


