#!/usr/bin/env python3
"""
Daily Automated Scraper for CLAVE.AI
Runs automatically via GitHub Actions cron, selecting URL based on day of week.
"""

import asyncio
import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# 28 NICHOS - Rotación por semana del mes (1-4) y día de la semana (0-6)
# =============================================================================
NICHOS = {
    # SEMANA 1 (días 1-7 del mes)
    (1, 0): "veterinaria",
    (1, 1): "escuela+de+idiomas",
    (1, 2): "restaurante",
    (1, 3): "cafeteria",
    (1, 4): "estudio+de+fotografia",
    (1, 5): "floristeria",
    (1, 6): "taller+mecanico",
    
    # SEMANA 2 (días 8-14 del mes)
    (2, 0): "cerrajeria",
    (2, 1): "agencia+de+viajes",
    (2, 2): "escuela+de+baile",
    (2, 3): "tienda+de+mascotas",
    (2, 4): "optica",
    (2, 5): "farmacia",
    (2, 6): "papeleria",
    
    # SEMANA 3 (días 15-21 del mes)
    (3, 0): "imprenta",
    (3, 1): "lavanderia",
    (3, 2): "spa",
    (3, 3): "escuela+de+musica",
    (3, 4): "joyeria",
    (3, 5): "muebleria",
    (3, 6): "ferreteria",
    
    # SEMANA 4 (días 22-31 del mes)
    (4, 0): "clinica+dental",
    (4, 1): "nutriologo",
    (4, 2): "fisioterapia",
    (4, 3): "consultorio+medico",
    (4, 4): "salon+de+eventos",
    (4, 5): "escuela+de+manejo",
    (4, 6): "agencia+de+seguros",
}

# =============================================================================
# MENSAJES PERSONALIZADOS POR NICHO - Cada uno termina con pregunta abierta
# Mencionamos que somos empresa de IA para dar contexto de solución escalable
# =============================================================================
MENSAJES_POR_NICHO = {
    # SEMANA 1
    "veterinaria": {
        "mensaje": "Qué tal! Vi tu veterinaria {nombre} en Google Maps.\nSoy de CLAVE.AI, una empresa de inteligencia artificial que automatiza negocios.\nCreamos sistemas de recordatorios de citas y vacunas con IA.\n¿Actualmente cómo le haces para recordarle a tus clientes sus citas? 🐾",
        "followup": "Hola de nuevo! Te escribí hace unos días sobre automatizar {nombre} con IA.\n¿Te gustaría que te muestre cómo funciona en 5 min? Sin compromiso 👍"
    },
    "escuela+de+idiomas": {
        "mensaje": "Qué tal! Vi tu escuela {nombre} buscando negocios en la zona.\nSoy de CLAVE.AI, usamos inteligencia artificial para automatizar negocios.\nAyudamos a escuelas a conseguir más alumnos con seguimiento inteligente.\n¿Cómo consigues nuevos estudiantes actualmente? 📚",
        "followup": "Hola! Te contacté hace unos días sobre {nombre}.\n¿Tienes 5 min para platicar cómo la IA podría ayudarte a conseguir más alumnos?"
    },
    "restaurante": {
        "mensaje": "Qué tal! Vi tu restaurante {nombre} en Maps.\nSoy de CLAVE.AI, automatizamos negocios con inteligencia artificial.\nHacemos menús digitales, reservas y pedidos con IA integrada.\n¿Ya tienes menú con QR o sistema de pedidos? 🍽️",
        "followup": "Hola! Te escribí hace unos días sobre {nombre}.\n¿Te interesaría un sistema de pedidos con IA? Puedo mostrarte ejemplos rápido."
    },
    "cafeteria": {
        "mensaje": "Qué tal! Vi tu cafetería {nombre} en Google Maps.\nSoy de CLAVE.AI, usamos inteligencia artificial para automatizar negocios.\nCreamos programas de lealtad inteligentes y pedidos automatizados.\n¿Tienes algún sistema de puntos para clientes frecuentes? ☕",
        "followup": "Hola de nuevo! Te contacté sobre {nombre} hace unos días.\n¿Te gustaría ver cómo funciona un programa de lealtad con IA?"
    },
    "estudio+de+fotografia": {
        "mensaje": "Qué tal! Vi tu estudio {nombre} buscando fotógrafos en la zona.\nSoy de CLAVE.AI, empresa de inteligencia artificial para negocios.\nHacemos portafolios web y sistemas de reserva inteligentes.\n¿Cómo muestras tu trabajo a clientes nuevos actualmente? 📸",
        "followup": "Hola! Te escribí hace unos días sobre crear un portafolio web para {nombre}.\n¿Tienes 5 min para que te muestre algunos ejemplos?"
    },
    "floristeria": {
        "mensaje": "Qué tal! Vi tu florería {nombre} en Maps.\nSoy de CLAVE.AI, automatizamos negocios con inteligencia artificial.\nCreamos catálogos digitales y pedidos por WhatsApp automatizados.\n¿Cómo reciben pedidos actualmente, solo llamada o también WhatsApp? 💐",
        "followup": "Hola! Te contacté sobre {nombre} hace unos días.\n¿Te interesa ver cómo automatizar pedidos con IA?"
    },
    "taller+mecanico": {
        "mensaje": "Qué tal! Vi tu taller {nombre} en Google Maps.\nSoy de CLAVE.AI, usamos inteligencia artificial para automatizar negocios.\nHacemos sistemas de citas y recordatorios de servicio inteligentes.\n¿Cómo le haces para que tus clientes regresen a su próximo servicio? 🔧",
        "followup": "Hola de nuevo! Te escribí sobre {nombre} hace unos días.\n¿Te gustaría ver cómo funcionan los recordatorios automáticos con IA?"
    },
    
    # SEMANA 2
    "cerrajeria": {
        "mensaje": "Qué tal! Vi tu cerrajería {nombre} en Maps.\nSoy de CLAVE.AI, empresa de inteligencia artificial para negocios.\nHacemos páginas web con llamada directa y ubicación optimizada.\n¿La mayoría de tus clientes te encuentran por Google o por recomendación? 🔑",
        "followup": "Hola! Te contacté hace unos días sobre {nombre}.\n¿Te interesaría aparecer mejor en Google con ayuda de IA?"
    },
    "agencia+de+viajes": {
        "mensaje": "Qué tal! Vi tu agencia {nombre} buscando negocios en la zona.\nSoy de CLAVE.AI, automatizamos negocios con inteligencia artificial.\nCreamos seguimiento automático de clientes con IA.\n¿Cómo le das seguimiento a la gente que pregunta pero no compra de inmediato? ✈️",
        "followup": "Hola! Te escribí hace días sobre automatizar seguimiento en {nombre} con IA.\n¿Tienes 5 min para platicar?"
    },
    "escuela+de+baile": {
        "mensaje": "Qué tal! Vi tu escuela {nombre} en Google Maps.\nSoy de CLAVE.AI, usamos inteligencia artificial para automatizar negocios.\nHacemos sistemas de inscripción y recordatorios inteligentes.\n¿Cómo manejan las inscripciones actualmente, presencial o tienen algo online? 💃",
        "followup": "Hola de nuevo! Te contacté sobre {nombre} hace unos días.\n¿Te interesaría un sistema de inscripción automatizado con IA?"
    },
    "tienda+de+mascotas": {
        "mensaje": "Qué tal! Vi tu tienda {nombre} en Maps.\nSoy de CLAVE.AI, empresa de inteligencia artificial para negocios.\nHacemos tiendas online con recordatorios de compra inteligentes.\n¿Tus clientes pueden comprarte por WhatsApp o solo en tienda? 🐕",
        "followup": "Hola! Te escribí sobre {nombre} hace unos días.\n¿Te gustaría ver cómo funciona una tienda con IA integrada?"
    },
    "optica": {
        "mensaje": "Qué tal! Vi tu óptica {nombre} buscando negocios en la zona.\nSoy de CLAVE.AI, automatizamos negocios con inteligencia artificial.\nCreamos sistemas de citas y recordatorios de revisión con IA.\n¿Cómo agendan citas tus clientes actualmente? 👓",
        "followup": "Hola! Te contacté hace días sobre automatizar citas en {nombre}.\n¿Tienes 5 min para que te cuente cómo funciona la IA?"
    },
    "farmacia": {
        "mensaje": "Qué tal! Vi tu farmacia {nombre} en Google Maps.\nSoy de CLAVE.AI, usamos inteligencia artificial para automatizar negocios.\nHacemos catálogos digitales y pedidos automatizados.\n¿Hacen entregas a domicilio o solo venta en mostrador? 💊",
        "followup": "Hola! Te escribí sobre {nombre} hace unos días.\n¿Te interesaría automatizar pedidos y entregas con IA?"
    },
    "papeleria": {
        "mensaje": "Qué tal! Vi tu papelería {nombre} en Maps.\nSoy de CLAVE.AI, empresa de inteligencia artificial para negocios.\nCreamos catálogos online y pedidos automatizados.\n¿Tus clientes pueden ver qué productos tienes antes de ir a la tienda? 📎",
        "followup": "Hola de nuevo! Te contacté sobre {nombre} hace días.\n¿Te gustaría un catálogo digital inteligente?"
    },
    
    # SEMANA 3
    "imprenta": {
        "mensaje": "Qué tal! Vi tu imprenta {nombre} buscando negocios en la zona.\nSoy de CLAVE.AI, automatizamos negocios con inteligencia artificial.\nHacemos cotizadores automáticos con IA para imprentas.\n¿Cómo reciben las solicitudes de cotización actualmente? 🖨️",
        "followup": "Hola! Te escribí hace días sobre automatizar cotizaciones en {nombre}.\n¿Te interesaría ver cómo funciona un cotizador con IA?"
    },
    "lavanderia": {
        "mensaje": "Qué tal! Vi tu lavandería {nombre} en Google Maps.\nSoy de CLAVE.AI, usamos inteligencia artificial para automatizar negocios.\nCreamos sistemas de seguimiento y notificaciones inteligentes.\n¿Tus clientes pueden saber cuándo está lista su ropa sin llamar? 🧺",
        "followup": "Hola! Te contacté sobre {nombre} hace unos días.\n¿Te gustaría que tus clientes reciban avisos automáticos con IA?"
    },
    "spa": {
        "mensaje": "Qué tal! Vi tu spa {nombre} en Maps.\nSoy de CLAVE.AI, empresa de inteligencia artificial para negocios.\nHacemos sistemas de reservas y recordatorios inteligentes.\n¿Cómo agendan citas tus clientes, por llamada o WhatsApp? 💆",
        "followup": "Hola de nuevo! Te escribí sobre {nombre} hace días.\n¿Te interesaría un sistema de reservas con IA?"
    },
    "escuela+de+musica": {
        "mensaje": "Qué tal! Vi tu escuela {nombre} buscando negocios en la zona.\nSoy de CLAVE.AI, automatizamos negocios con inteligencia artificial.\nCreamos sistemas de inscripción y seguimiento de alumnos.\n¿Cómo consigues nuevos alumnos actualmente? 🎸",
        "followup": "Hola! Te contacté hace días sobre {nombre}.\n¿Tienes 5 min para platicar sobre cómo la IA puede ayudarte?"
    },
    "joyeria": {
        "mensaje": "Qué tal! Vi tu joyería {nombre} en Google Maps.\nSoy de CLAVE.AI, usamos inteligencia artificial para automatizar negocios.\nHacemos catálogos digitales elegantes y tiendas online.\n¿Tus clientes pueden ver tu catálogo completo online? 💎",
        "followup": "Hola! Te escribí sobre {nombre} hace unos días.\n¿Te gustaría ver ejemplos de catálogos con IA?"
    },
    "muebleria": {
        "mensaje": "Qué tal! Vi tu mueblería {nombre} en Maps.\nSoy de CLAVE.AI, empresa de inteligencia artificial para negocios.\nCreamos catálogos digitales y cotizadores inteligentes.\n¿Tus clientes pueden ver tus muebles online antes de visitarte? 🛋️",
        "followup": "Hola de nuevo! Te contacté sobre {nombre} hace días.\n¿Te interesaría un catálogo digital con IA?"
    },
    "ferreteria": {
        "mensaje": "Qué tal! Vi tu ferretería {nombre} buscando negocios en la zona.\nSoy de CLAVE.AI, automatizamos negocios con inteligencia artificial.\nHacemos catálogos digitales y pedidos automatizados.\n¿Tus clientes pueden consultar si tienes un producto antes de ir? 🔨",
        "followup": "Hola! Te escribí hace días sobre {nombre}.\n¿Te gustaría que tus clientes consulten inventario con IA?"
    },
    
    # SEMANA 4
    "clinica+dental": {
        "mensaje": "Qué tal! Vi tu clínica {nombre} en Google Maps.\nSoy de CLAVE.AI, usamos inteligencia artificial para automatizar negocios.\nCreamos sistemas de citas y recordatorios inteligentes.\n¿Cómo agendan citas tus pacientes actualmente? 🦷",
        "followup": "Hola! Te contacté hace días sobre {nombre}.\n¿Te interesaría automatizar recordatorios con IA?"
    },
    "nutriologo": {
        "mensaje": "Qué tal! Vi tu consultorio {nombre} en Maps.\nSoy de CLAVE.AI, empresa de inteligencia artificial para negocios.\nHacemos sistemas de citas y seguimiento de pacientes con IA.\n¿Cómo le das seguimiento a tus pacientes entre consultas? 🥗",
        "followup": "Hola de nuevo! Te escribí sobre {nombre} hace días.\n¿Te gustaría ver cómo automatizar seguimiento con IA?"
    },
    "fisioterapia": {
        "mensaje": "Qué tal! Vi tu clínica {nombre} buscando negocios en la zona.\nSoy de CLAVE.AI, automatizamos negocios con inteligencia artificial.\nCreamos sistemas de citas y seguimiento de tratamientos.\n¿Cómo agendan sus sesiones tus pacientes? 💪",
        "followup": "Hola! Te contacté hace días sobre {nombre}.\n¿Te interesaría un sistema de citas con IA?"
    },
    "consultorio+medico": {
        "mensaje": "Qué tal! Vi tu consultorio {nombre} en Google Maps.\nSoy de CLAVE.AI, usamos inteligencia artificial para automatizar negocios.\nHacemos sistemas de citas online y recordatorios inteligentes.\n¿Tus pacientes pueden agendar cita online o solo por teléfono? 🏥",
        "followup": "Hola! Te escribí sobre {nombre} hace unos días.\n¿Te gustaría que tus pacientes agenden con IA?"
    },
    "salon+de+eventos": {
        "mensaje": "Qué tal! Vi tu salón {nombre} en Maps.\nSoy de CLAVE.AI, empresa de inteligencia artificial para negocios.\nCreamos páginas web con galería y cotizadores inteligentes.\n¿Cómo muestras tus espacios a clientes que preguntan? 🎉",
        "followup": "Hola de nuevo! Te contacté sobre {nombre} hace días.\n¿Te interesaría una página web con cotizador IA?"
    },
    "escuela+de+manejo": {
        "mensaje": "Qué tal! Vi tu escuela {nombre} buscando negocios en la zona.\nSoy de CLAVE.AI, automatizamos negocios con inteligencia artificial.\nHacemos sistemas de inscripción y seguimiento inteligentes.\n¿Cómo se inscriben tus alumnos actualmente? 🚗",
        "followup": "Hola! Te escribí hace días sobre {nombre}.\n¿Te gustaría un sistema de inscripción con IA?"
    },
    "agencia+de+seguros": {
        "mensaje": "Qué tal! Vi tu agencia {nombre} en Google Maps.\nSoy de CLAVE.AI, usamos inteligencia artificial para automatizar negocios.\nCreamos sistemas de seguimiento y cotizadores con IA.\n¿Cómo le das seguimiento a tus prospectos actualmente? 📋",
        "followup": "Hola! Te contacté sobre {nombre} hace unos días.\n¿Te interesaría automatizar el seguimiento con IA?"
    },
}

# Mensaje genérico de respaldo
MENSAJE_DEFAULT = {
    "mensaje": "Qué tal! Encontré {nombre} buscando negocios en la zona.\nSoy de CLAVE.AI, una empresa de inteligencia artificial que automatiza negocios.\nCreamos soluciones digitales escalables para negocios locales.\n¿Cómo consigues clientes nuevos actualmente? 🚀",
    "followup": "Hola! Te escribí hace unos días sobre {nombre}.\nSomos CLAVE.AI, ¿tienes 5 min para platicar? Sin compromiso 👍"
}

# =============================================================================
# 12 ZONAS DE GUADALAJARA - Rotación por mes
# =============================================================================
ZONAS_GDL = {
    1:  {"nombre": "Centro GDL",       "lat": 20.6767, "lng": -103.3475, "zoom": 14},
    2:  {"nombre": "Zapopan Centro",   "lat": 20.7214, "lng": -103.3863, "zoom": 14},
    3:  {"nombre": "Tlaquepaque",      "lat": 20.6409, "lng": -103.3127, "zoom": 14},
    4:  {"nombre": "Tonalá",           "lat": 20.6249, "lng": -103.2345, "zoom": 14},
    5:  {"nombre": "Providencia",      "lat": 20.7002, "lng": -103.3921, "zoom": 14},
    6:  {"nombre": "Chapultepec",      "lat": 20.6871, "lng": -103.3678, "zoom": 14},
    7:  {"nombre": "Americana",        "lat": 20.6726, "lng": -103.3621, "zoom": 14},
    8:  {"nombre": "Santa Tere",       "lat": 20.6654, "lng": -103.3512, "zoom": 14},
    9:  {"nombre": "Oblatos",          "lat": 20.6923, "lng": -103.3201, "zoom": 14},
    10: {"nombre": "Medrano",          "lat": 20.6612, "lng": -103.3289, "zoom": 14},
    11: {"nombre": "Mezquitan",        "lat": 20.6945, "lng": -103.3567, "zoom": 14},
    12: {"nombre": "Miravalle",        "lat": 20.6321, "lng": -103.3012, "zoom": 14},
}

def get_daily_url(day_override=None, zone_offset=0):
    """
    Genera la URL de Google Maps basada en:
    - Semana del mes (1-4) + Día de la semana (0-6) -> Determina el NICHO
    - Mes del año (1-12) + zone_offset -> Determina la ZONA geográfica
    
    Esto da 28 nichos × 12 zonas = 336 combinaciones únicas
    
    Args:
        day_override: Override para el día de la semana (0-6)
        zone_offset: Offset para probar zonas adicionales (0-11), útil para fallback
    """
    today = datetime.now()
    
    # Calcular semana del mes (1-4)
    day_of_month = today.day
    if day_of_month <= 7:
        week_of_month = 1
    elif day_of_month <= 14:
        week_of_month = 2
    elif day_of_month <= 21:
        week_of_month = 3
    else:
        week_of_month = 4
    
    # Día de la semana (0=Lunes, 6=Domingo)
    if day_override is not None:
        try:
            day_of_week = int(day_override)
            print(f"[CONFIG] Overriding day of week with: {day_of_week}")
        except:
            day_of_week = today.weekday()
    else:
        day_of_week = today.weekday()
    
    # Mes del año (1-12) + zone_offset para fallback
    base_month = today.month
    # Rotar entre las 12 zonas usando el offset
    effective_zone = ((base_month - 1 + zone_offset) % 12) + 1
    
    # Obtener nicho y zona
    nicho = NICHOS.get((week_of_month, day_of_week), "negocio+local")
    zona = ZONAS_GDL.get(effective_zone, ZONAS_GDL[1])
    
    # Construir URL con zoom más amplio (13z en vez de 14z) para más resultados
    zoom = 13 if zone_offset > 0 else zona['zoom']
    url = f"https://www.google.com.mx/maps/search/{nicho}/@{zona['lat']},{zona['lng']},{zoom}z"
    
    return {
        "url": url,
        "nicho": nicho.replace("+", " "),
        "zona": zona["nombre"],
        "semana": week_of_month,
        "dia": day_of_week,
        "mes": base_month,
        "zone_offset": zone_offset,
        "effective_zone": effective_zone
    }

import random
import httpx
from playwright.async_api import async_playwright

# Import analyzer if available
try:
    from analyzer import ai_analyzer
    HAS_ANALYZER = True
except ImportError:
    HAS_ANALYZER = False
    print("[WARN] AI Analyzer not available, using template messages")


# =============================================================================
# SISTEMA DE TRACKING - Evita contactar el mismo teléfono dos veces
# =============================================================================
class LeadTracker:
    """
    Mantiene un registro de todos los teléfonos ya contactados.
    Persiste los datos en un archivo JSON para mantener el historial.
    Ahora incluye fecha de contacto para sistema de follow-up.
    """
    
    def __init__(self, tracking_file="contacted_leads.json"):
        self.tracking_file = os.path.join(os.path.dirname(__file__), tracking_file)
        self.contacted_phones = set()
        self.leads_data = {}  # phone -> {contact_date, lead_name, followup_message, followup_sent}
        self._load_tracking_data()
    
    def _load_tracking_data(self):
        """Carga los teléfonos ya contactados desde el archivo"""
        try:
            if os.path.exists(self.tracking_file):
                with open(self.tracking_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.contacted_phones = set(data.get("phones", []))
                    self.leads_data = data.get("leads_data", {})
                    print(f"[TRACKER] Loaded {len(self.contacted_phones)} previously contacted phones")
            else:
                print("[TRACKER] No previous tracking data found, starting fresh")
        except Exception as e:
            print(f"[TRACKER] Error loading tracking data: {e}")
            self.contacted_phones = set()
            self.leads_data = {}
    
    def _save_tracking_data(self):
        """Guarda los teléfonos contactados al archivo"""
        try:
            data = {
                "phones": list(self.contacted_phones),
                "leads_data": self.leads_data,
                "total_count": len(self.contacted_phones),
                "last_updated": datetime.now().isoformat()
            }
            with open(self.tracking_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"[TRACKER] Saved {len(self.contacted_phones)} phones to tracking file")
        except Exception as e:
            print(f"[TRACKER] Error saving tracking data: {e}")
    
    def is_contacted(self, phone: str) -> bool:
        """Verifica si un teléfono ya fue contactado"""
        return phone in self.contacted_phones
    
    def mark_as_contacted(self, phone: str):
        """Marca un teléfono como contactado"""
        self.contacted_phones.add(phone)
    
    def filter_new_leads(self, leads: list) -> tuple:
        """
        Filtra leads que ya fueron contactados.
        Retorna: (leads_nuevos, leads_duplicados)
        """
        new_leads = []
        duplicate_leads = []
        
        for lead in leads:
            phone = lead.get("phone", "")
            if phone and not self.is_contacted(phone):
                new_leads.append(lead)
            else:
                duplicate_leads.append(lead)
        
        return new_leads, duplicate_leads
    
    def add_contacted_leads(self, leads: list):
        """Agrega una lista de leads al tracking con información para follow-up"""
        contact_date = datetime.now().isoformat()
        for lead in leads:
            phone = lead.get("phone", "")
            if phone:
                self.mark_as_contacted(phone)
                # Guardar datos para follow-up
                self.leads_data[phone] = {
                    "contact_date": contact_date,
                    "lead_name": lead.get("lead_name", ""),
                    "followup_message": lead.get("followup_message", ""),
                    "followup_sent": False,
                    "nicho": lead.get("nicho", "")
                }
        self._save_tracking_data()
    
    def get_leads_for_followup(self, days_since_contact=3):
        """Obtiene leads que necesitan follow-up (contactados hace X días y sin followup enviado)"""
        from datetime import timedelta
        now = datetime.now()
        leads_to_followup = []
        
        for phone, data in self.leads_data.items():
            if data.get("followup_sent", False):
                continue  # Ya se envió follow-up
            
            try:
                contact_date = datetime.fromisoformat(data.get("contact_date", ""))
                days_passed = (now - contact_date).days
                
                if days_passed >= days_since_contact:
                    leads_to_followup.append({
                        "phone": phone,
                        "message": data.get("followup_message", ""),
                        "lead_name": data.get("lead_name", ""),
                        "days_since_contact": days_passed
                    })
            except:
                continue
        
        return leads_to_followup
    
    def mark_followup_sent(self, phones: list):
        """Marca los follow-ups como enviados"""
        for phone in phones:
            if phone in self.leads_data:
                self.leads_data[phone]["followup_sent"] = True
        self._save_tracking_data()
    
    def get_stats(self) -> dict:
        """Retorna estadísticas del tracking"""
        pending_followups = len([p for p, d in self.leads_data.items() if not d.get("followup_sent", False)])
        return {
            "total_contacted": len(self.contacted_phones),
            "pending_followups": pending_followups,
            "tracking_file": self.tracking_file
        }


class AutomatedScraper:
    def __init__(self, nicho=""):
        # Clean webhook URL from any whitespace/newlines
        raw_url = os.getenv("N8N_WEBHOOK_URL", "")
        self.n8n_webhook_url = raw_url.strip().replace("\n", "").replace("\r", "") if raw_url else None
        self.max_leads = int(os.getenv("MAX_LEADS", "10"))
        self.delay_min = int(os.getenv("DELAY_MIN_MS", "2000"))
        self.delay_max = int(os.getenv("DELAY_MAX_MS", "5000"))
        self.leads = []
        # Nicho actual para mensajes personalizados
        self.current_nicho = nicho
        # Initialize lead tracker to avoid contacting duplicates
        self.tracker = LeadTracker()
        
        # Evolution API config para verificar WhatsApp
        self.evolution_url = os.getenv("EVOLUTION_API_URL", "https://evolutionapi-evolution-api.ckoomq.easypanel.host")
        self.evolution_key = os.getenv("EVOLUTION_API_KEY", "")
        self.evolution_instance = os.getenv("EVOLUTION_INSTANCE", "claveai")
    
    async def check_whatsapp(self, phone: str) -> bool:
        """Verifica si un número tiene WhatsApp usando Evolution API"""
        if not self.evolution_key:
            print(f"[WARN] No EVOLUTION_API_KEY configured, skipping WhatsApp check")
            return True  # Si no hay key, asumir que sí tiene
        
        try:
            url = f"{self.evolution_url}/chat/whatsappNumbers/{self.evolution_instance}"
            headers = {
                "apikey": self.evolution_key,
                "Content-Type": "application/json"
            }
            payload = {"numbers": [phone]}
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers, timeout=15.0)
                
                if response.status_code == 200:
                    data = response.json()
                    # Evolution API devuelve lista de resultados
                    if isinstance(data, list) and len(data) > 0:
                        exists = data[0].get("exists", False)
                        print(f"[WHATSAPP] {phone} -> {'✅ SÍ tiene' if exists else '❌ NO tiene'}")
                        return exists
                    return False
                else:
                    print(f"[WHATSAPP] Error checking {phone}: {response.status_code}")
                    return False
        except Exception as e:
            print(f"[WHATSAPP] Exception checking {phone}: {e}")
            return False  # En caso de error, descartar el número
        
    def clean_lead(self, lead):
        """Clean a lead's data from whitespace and newlines"""
        raw_phone = lead.get("phone", "")
        # Remove all non-digit characters (including +, spaces, dashes, etc.)
        clean_phone = "".join(filter(str.isdigit, raw_phone))
        
        # Normalize to Evolution API format: 52XXXXXXXXXX (no +, just digits)
        if len(clean_phone) == 10:
            # Local format (no country code) -> add 52
            clean_phone = "52" + clean_phone
        elif len(clean_phone) == 12 and clean_phone.startswith("52"):
            # Already has 52 prefix -> keep as is
            pass
        elif len(clean_phone) == 13 and clean_phone.startswith("521"):
            # Has 521 (old mobile format) -> convert to 52
            clean_phone = "52" + clean_phone[3:]
        elif len(clean_phone) > 12 and clean_phone.startswith("52"):
            # Too long but starts with 52 -> trim to 12 digits
            clean_phone = clean_phone[:12]
        
        return {
            "phone": clean_phone,
            "message": " ".join(lead.get("ai_analysis", "").split()),
            "followup_message": " ".join(lead.get("followup_message", "").split()),
            "lead_name": " ".join(lead.get("name", "").split()),
            "category": " ".join(lead.get("category", "").split()),
            "nicho": lead.get("nicho", ""),
            "website": lead.get("website", "").strip(),
            "google_maps_url": lead.get("google_maps_url", "").strip()
        }
        
    async def send_all_to_n8n(self, leads_list):
        """Send ALL leads to n8n webhook in a single call, filtering duplicates"""
        if not self.n8n_webhook_url:
            print(f"[WARN] No N8N_WEBHOOK_URL configured")
            return False
        
        # Filter leads with phone and clean them
        cleaned_leads = []
        for lead in leads_list:
            cleaned = self.clean_lead(lead)
            if cleaned["phone"]:  # Only include leads with phone
                cleaned_leads.append(cleaned)
        
        if not cleaned_leads:
            print(f"[WARN] No leads with phone numbers to send")
            return False
        
        # =====================================================================
        # FILTRAR DUPLICADOS - Evitar contactar el mismo teléfono dos veces
        # =====================================================================
        new_leads, duplicate_leads = self.tracker.filter_new_leads(cleaned_leads)
        
        if duplicate_leads:
            print(f"[TRACKER] ⚠️  Filtered out {len(duplicate_leads)} already contacted leads")
            for dup in duplicate_leads:
                print(f"    - {dup.get('lead_name', 'N/A')} ({dup.get('phone', 'N/A')})")
        
        if not new_leads:
            print(f"[TRACKER] ℹ️  All leads were already contacted. No new leads to send.")
            return True  # Not an error, just no new leads
        
        print(f"[TRACKER] ✅ {len(new_leads)} NEW leads to contact (out of {len(cleaned_leads)} total)")
        
        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "leads": new_leads,  # Only send NEW leads
                    "total_count": len(new_leads),
                    "source": "automated_scraper",
                    "timestamp": datetime.now().isoformat()
                }
                
                # Retry logic with exponential backoff
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        response = await client.post(self.n8n_webhook_url, json=payload, timeout=60.0)
                        print(f"[N8N] Sent {len(new_leads)} NEW leads in ONE call | Status: {response.status_code}")
                        
                        # Si el envío fue exitoso, registrar los leads como contactados
                        if response.status_code == 200:
                            self.tracker.add_contacted_leads(new_leads)
                            stats = self.tracker.get_stats()
                            print(f"[TRACKER] 📊 Total histórico de leads contactados: {stats['total_contacted']}")
                        
                        return response.status_code == 200
                    except httpx.TimeoutException as timeout_err:
                        if attempt < max_retries - 1:
                            wait_time = (attempt + 1) * 10  # 10s, 20s, 30s
                            print(f"[RETRY] Timeout on attempt {attempt + 1}/{max_retries}, waiting {wait_time}s...")
                            await asyncio.sleep(wait_time)
                        else:
                            raise timeout_err
        except Exception as e:
            print(f"[ERROR] Failed to send to n8n: {type(e).__name__}: {e}")
            return False

    async def get_text(self, page, selector) -> str:
        try:
            element = page.locator(selector).first
            if await element.is_visible(timeout=2000):
                return (await element.inner_text()).strip()
        except:
            return ""
        return ""

    async def get_attr(self, page, selector, attr) -> str:
        try:
            element = page.locator(selector).first
            if await element.is_visible(timeout=2000):
                return await element.get_attribute(attr)
        except:
            return ""
        return ""

    async def extract_details(self, page, url) -> dict:
        """Extract business details from Google Maps panel"""
        name_selector = 'h1.DUwDvf'
        category_selector = 'button.DkEaL'
        address_selector = 'button[data-item-id="address"]'
        phone_selector = 'button[data-item-id*="phone:tel:"]'
        website_selector = 'a[data-item-id="authority"]'

        await page.wait_for_selector(name_selector, timeout=10000)

        details = {
            "name": await self.get_text(page, name_selector),
            "category": await self.get_text(page, category_selector),
            "address": await self.get_text(page, address_selector),
            "phone": await self.get_text(page, phone_selector),
            "website": await self.get_attr(page, website_selector, "href"),
            "google_maps_url": url,
            "website_snippet": "",
            "ai_analysis": ""
        }
        
        # Try to get website snippet for AI analysis
        if details["website"]:
            try:
                site_page = await page.context.new_page()
                await site_page.goto(details["website"], wait_until="domcontentloaded", timeout=10000)
                details["website_snippet"] = (await site_page.inner_text("body"))[:1500]
                await site_page.close()
            except:
                details["website_snippet"] = "Could not load website."
        
        # =====================================================================
        # MENSAJES PERSONALIZADOS POR NICHO - con pregunta abierta al final
        # =====================================================================
        # Obtener el nicho actual (con + para coincidir con las keys del diccionario)
        nicho_key = self.current_nicho.replace(" ", "+") if self.current_nicho else ""
        
        # Buscar mensaje personalizado para este nicho
        mensaje_config = MENSAJES_POR_NICHO.get(nicho_key, MENSAJE_DEFAULT)
        
        # Generar mensaje personalizado con el nombre del negocio
        mensaje = mensaje_config["mensaje"].format(nombre=details['name'])
        mensaje_followup = mensaje_config["followup"].format(nombre=details['name'])
        
        details["ai_analysis"] = mensaje
        details["followup_message"] = mensaje_followup
        details["nicho"] = self.current_nicho
        
        # Try AI analysis if available (override mensaje personalizado)
        if HAS_ANALYZER and details["website_snippet"] and details["website_snippet"] != "Could not load website.":
            try:
                analysis = await ai_analyzer.analyze_business(
                    details["name"], details["category"], details["website_snippet"]
                )
                if "Error" not in analysis:
                    details["ai_analysis"] = analysis
            except:
                pass
                
        return details

    async def scrape_url(self, url: str):
        """Scrape a single Google Maps URL"""
        print(f"\n{'='*60}")
        print(f"[START] Scraping: {url[:80]}...")
        print(f"[CONFIG] Max leads: {self.max_leads}, Delay: {self.delay_min}-{self.delay_max}ms")
        print(f"{'='*60}\n")
        
        async with async_playwright() as p:
            # HEADLESS for CI/CD environments
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(5)
                
                # Handle cookie consent
                try:
                    consent_btn = page.locator('button[aria-label*="Accept"], button[aria-label*="Aceptar"]')
                    if await consent_btn.is_visible(timeout=3000):
                        await consent_btn.click()
                except:
                    pass

                leads_count = 0
                processed_urls = set()
                sent_count = 0

                processed_count = 0
                max_attempts = self.max_leads * 5  # No buscar infinitamente, máximo 5x el límite

                while leads_count < self.max_leads and processed_count < max_attempts:
                    links = await page.locator('a[href*="/maps/place/"]').all()
                    
                    if not links:
                        await page.mouse.wheel(0, 3000)
                        await asyncio.sleep(2)
                        links = await page.locator('a[href*="/maps/place/"]').all()
                        if not links:
                            break

                    for link in links:
                        if leads_count >= self.max_leads or processed_count >= max_attempts:
                            break
                        
                        href = await link.get_attribute("href")
                        if href in processed_urls:
                            continue
                            
                        processed_urls.add(href)
                        processed_count += 1
                        
                        try:
                            # Hacer scroll al elemento para que sea visible
                            await link.scroll_into_view_if_needed()
                            await link.click()
                            await asyncio.sleep(random.randint(self.delay_min, self.delay_max) / 1000)
                            
                            lead = await self.extract_details(page, href)
                            
                            # Verificar si tiene teléfono y no ha sido contactado
                            cleaned = self.clean_lead(lead)
                            if not cleaned["phone"]:
                                print(f"[SKIP] {lead['name']} | SIN TELÉFONO")
                                continue
                            
                            if self.tracker.is_contacted(cleaned["phone"]):
                                print(f"[SKIP] {lead['name']} | DUPLICADO")
                                continue
                            
                            # =========================================================
                            # VERIFICAR SI TIENE WHATSAPP con Evolution API
                            # =========================================================
                            has_whatsapp = await self.check_whatsapp(cleaned["phone"])
                            if not has_whatsapp:
                                print(f"[SKIP] {lead['name']} | NO TIENE WHATSAPP ❌")
                                continue  # No lo contamos, buscar otro
                            
                            # ¡Tiene WhatsApp! Agregarlo como lead válido
                            self.leads.append(lead)
                            leads_count += 1
                            print(f"[LEAD {leads_count}] {lead['name']} | Phone: {lead['phone']} ✅ TIENE WHATSAPP")
                                     
                        except Exception as e:
                            print(f"[ERROR] Extracting lead: {e}")
                            continue

                    # Scroll for more para la siguiente iteración si aún faltan leads
                    if leads_count < self.max_leads:
                        await page.mouse.wheel(0, 2000)
                        await asyncio.sleep(2)
                    
                    # Check end of list
                    try:
                        if await page.locator('text="You\'ve reached the end of the list"').is_visible():
                            print("[INFO] Reached end of Google Maps list")
                            break
                    except:
                        pass

                # Send ALL leads to n8n in ONE call at the end
                if self.leads:
                    success = await self.send_all_to_n8n(self.leads)
                    sent_count = len([l for l in self.leads if l.get("phone")]) if success else 0

                print(f"\n{'='*60}")
                print(f"[DONE] Extracted: {leads_count} leads | Sent to n8n: {sent_count} (in 1 call)")
                print(f"{'='*60}\n")
                
            except Exception as e:
                print(f"[FATAL ERROR] {e}")
            finally:
                await browser.close()
                
        return self.leads


async def main():
    # Obtener override de día si se pasa por argumento
    day_arg = sys.argv[1] if len(sys.argv) > 1 else None
    today = datetime.now()
    day_names = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    
    print(f"\n🚀 CLAVE.AI Automated Lead Scraper v2.2 (con fallback de zonas)")
    print(f"{'='*60}")
    
    # =========================================================================
    # ESTRATEGIA DE FALLBACK: Si no hay leads nuevos, probar otras zonas
    # =========================================================================
    MAX_ZONE_ATTEMPTS = 4  # Probar hasta 4 zonas diferentes
    total_new_leads = 0
    
    for zone_offset in range(MAX_ZONE_ATTEMPTS):
        # Obtener URL dinámica basada en día + semana + mes + zone_offset
        config = get_daily_url(day_override=day_arg, zone_offset=zone_offset)
        
        print(f"\n{'='*60}")
        print(f"📅 Fecha Actual: {today.strftime('%Y-%m-%d %H:%M')}")
        print(f"📆 Día a procesar: {day_names[config['dia']]} (Semana {config['semana']} del mes)")
        print(f"🏪 Nicho: {config['nicho'].upper()}")
        print(f"📍 Zona: {config['zona']} {'(FALLBACK #'+str(zone_offset)+')' if zone_offset > 0 else '(PRIMARIA)'}")
        print(f"🔗 URL: {config['url'][:80]}...")
        print(f"📡 Webhook: {os.getenv('N8N_WEBHOOK_URL', 'NOT SET')[:50]}...")
        print(f"{'='*60}")
        
        scraper = AutomatedScraper(nicho=config['nicho'])
        leads = await scraper.scrape_url(config['url'])
        
        # Contar leads NUEVOS que realmente se enviaron
        # (los que pasaron el filtro de duplicados)
        new_leads_sent = len([l for l in leads if l.get("phone")])
        
        if new_leads_sent > 0:
            total_new_leads += new_leads_sent
            print(f"\n✅ ¡Éxito! Enviados {new_leads_sent} leads nuevos desde {config['zona']}")
            break  # Encontramos leads, no necesitamos más fallback
        else:
            if zone_offset < MAX_ZONE_ATTEMPTS - 1:
                print(f"\n⚠️ No se encontraron leads NUEVOS en {config['zona']}")
                print(f"🔄 Probando siguiente zona de fallback...")
            else:
                print(f"\n❌ Se agotaron todas las zonas de fallback sin encontrar leads nuevos")
    
    print(f"\n{'='*60}")
    print(f"📊 RESUMEN FINAL")
    print(f"{'='*60}")
    print(f"✅ Total leads nuevos enviados: {total_new_leads}")
    print(f"📊 Combinación base: Mes {config['mes']} + Semana {config['semana']} + Día {config['dia']}")
    print(f"📍 Zonas intentadas: {zone_offset + 1}")
    print(f"{'='*60}\n")

    

if __name__ == "__main__":
    asyncio.run(main())

