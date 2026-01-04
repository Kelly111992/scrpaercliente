import httpx
import asyncio
import json
import os
from dotenv import load_dotenv

load_dotenv()

class AIAnalyzer:
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.url = "https://openrouter.ai/api/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def analyze_business(self, business_name: str, category: str, website_text: str):
        if not self.api_key:
            return "API Key not configured."

        if not website_text or website_text == "Could not load website.":
            prompt = f"""
            Actúa como un Visionario Tecnológico de CLAVE.AI. 
            El negocio "{business_name}" ({category}) NO tiene sitio web o presencia digital clara.
            
            TAREA:
            1. DEFICIT: Falta de presencia digital clara o web obsoleta.
            2. MENSAJE PERSUASIVO (WhatsApp): Escribe un mensaje corto y potente para contactar al dueño.
               - Inicia con un cumplido genuino sobre su negocio "{business_name}".
               - IMPORTANTE: NO incluyas links de Google Maps ni links externos del propio cliente en el mensaje.
               - Menciona de forma empática cómo la falta de una plataforma web profesional les hace perder oportunidades frente a la competencia.
               - Explica brevemente cómo la Inteligencia Artificial y la automatización en CLAVE.AI pueden ayudarlos a captar clientes 24/7.
               - Cierra con un CTA (Llamado a la acción) incluyendo únicamente los links de CLAVE.AI: Web: https://claveai.com.mx e Instagram: https://www.instagram.com/claveai/
            3. SERVICIO RECOMENDADO: Menciona el servicio más apto de CLAVE.AI.
            
            Tono: Profesional, visionario y cercano. Máximo 100 palabras.
            """
        else:
            prompt = f"""
            Actúa como Especialista en Estrategia Digital de CLAVE.AI. Analiza el negocio "{business_name}" ({category}).
            
            DATOS DEL PROSPECTO:
            CONTENIDO WEB (Resumen): {website_text[:2000]}
            
            TU OBJETIVO: Generar una propuesta de contacto irresistible via WhatsApp.
            
            TAREA:
            1. ANÁLISIS (Breve): Qué le falta a su web actual para convertir más.
            2. MENSAJE DE CONTACTO (WhatsApp):
               - Valida su presencia actual (ej: "Me gustó mucho su sección de...").
               - IMPORTANTE: NO incluyas links de Google Maps ni links externos del propio cliente.
               - Sugiere una mejora específica basada en IA o automatización que solo CLAVE.AI ofrece.
               - Al final, invita a conocer más en nuestra web https://claveai.com.mx y ver nuestro Instagram https://www.instagram.com/claveai/ para darles confianza.
            3. SERVICIO RECOMENDADO: Qué solución de CLAVE.AI les encaja mejor.
            
            REGLA DE ORO: Evita sonar como un script de ventas aburrido. Sé humano, experto y directo al valor.
            """

        payload = {
            "model": "google/gemini-2.0-flash-exp:free",
            "messages": [
                {"role": "system", "content": "Eres un experto en análisis de negocios y prospección de ventas."},
                {"role": "user", "content": prompt}
            ]
        }

        try:
            async with httpx.AsyncClient() as client:
                for attempt in range(3): # Try 3 times
                    response = await client.post(self.url, headers=self.headers, json=payload, timeout=30.0)
                    if response.status_code == 200:
                        result = response.json()
                        return result['choices'][0]['message']['content']
                    elif response.status_code == 429:
                        if attempt < 2:
                            wait_time = (attempt + 1) * 5
                            print(f"Rate limit hit. Waiting {wait_time}s...")
                            await asyncio.sleep(wait_time)
                            continue
                    return f"Error AI ({response.status_code}): {response.text}"
        except Exception as e:
            return f"Error conectando con AI: {str(e)}"

ai_analyzer = AIAnalyzer()
