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
            1. DEFICIT: Falta de presencia digital y automatización.
            2. MENSAJE SUTIL (Speech Potente): Escribe un mensaje corto y muy potente para WhatsApp.
               - Empieza con un cumplido sincero sobre su negocio.
               - Menciona de forma inspiradora cómo hoy en día no tener web es como ser invisible para nuevos clientes.
               - Introduce cómo la Inteligencia Artificial y la automatización podrían simplificarles la vida y atraer ventas en automático.
               - Cierra invitándoles a ver lo que haces en CLAVE.AI: https://www.instagram.com/claveai
            3. SERVICIO RECOMENDADO: Pack "Transformación Digital + IA".
            
            Tono: Inspirador, no regañón. Máximo 80 palabras.
            """
        else:
            prompt = f"""
            Actúa como un Especialista en Relaciones B2B para la agencia "CLAVE.AI" (https://www.instagram.com/claveai).
            Tu objetivo es analizar el siguiente negocio y sugerir una mejora sutil.
            
            DATOS DEL PROSPECTO:
            NEGOCIO: {business_name}
            CATEGORÍA: {category}
            CONTENIDO WEB (Resumen): {website_text[:2000]}
            
            TU IDENTIDAD: Representas a CLAVE.AI. Eres profesional, experto en IA y desarrollo web, pero muy cercano.
            
            TAREA:
            1. DEFICIT (Breve): Identifica el problema principal de su presencia web.
            2. MENSAJE SUTIL (WhatsApp/Email): Escribe una propuesta de contacto.
               - Valida algo positivo de ellos.
               - Menciona el déficit como una observación para mejorar su experiencia de cliente.
               - Al final, menciona suavemente que vienes de CLAVE.AI y que pueden ver tu trabajo en https://www.instagram.com/claveai.
            3. SERVICIO RECOMENDADO: Qué servicio de CLAVE.AI les ayudaría.
            
            REGLA DE ORO: Tono amigable y no invasivo. El enlace a Instagram sirve para darles seguridad de que eres una agencia real.
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
