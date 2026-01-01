#!/usr/bin/env python3
"""
Daily Automated Scraper for CLAVE.AI
Runs automatically via GitHub Actions cron, selecting URL based on day of week.
"""

import asyncio
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# URLs for each day of the week (0 = Monday, 6 = Sunday)
DAILY_URLS = {
    0: "https://www.google.com.mx/maps/search/salon+de+belleza/@20.6558451,-103.3240786,15z",  # Monday
    1: "https://www.google.com.mx/maps/search/terapeutas/@20.6558445,-103.3240786,15z",        # Tuesday
    2: "https://www.google.com.mx/maps/search/psicologos/@20.6558439,-103.3240786,15z",        # Wednesday
    3: "https://www.google.com.mx/maps/search/gimnasio/@20.6558432,-103.3240786,15z",          # Thursday
    4: "https://www.google.com.mx/maps/search/dentista/@20.6558426,-103.3240786,15z",          # Friday
    5: "https://www.google.com.mx/maps/search/inmobiliaria/@20.655842,-103.3240786,15z",       # Saturday
    6: "https://www.google.com.mx/maps/search/despachos+de+abogados/@20.6558368,-103.3549785,13z",  # Sunday
}

# Extra URLs for variety (can be used with --extra flag)
EXTRA_URLS = [
    "https://www.google.com.mx/maps/search/agencias+de+seguros/@20.6558368,-103.3549785,13z",
]

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


class AutomatedScraper:
    def __init__(self):
        self.n8n_webhook_url = os.getenv("N8N_WEBHOOK_URL")
        self.max_leads = int(os.getenv("MAX_LEADS", "10"))
        self.delay_min = int(os.getenv("DELAY_MIN_MS", "2000"))
        self.delay_max = int(os.getenv("DELAY_MAX_MS", "5000"))
        self.leads = []
        
    async def send_to_n8n(self, lead):
        """Send lead to n8n webhook for WhatsApp delivery"""
        if not self.n8n_webhook_url:
            print(f"[WARN] No N8N_WEBHOOK_URL configured")
            return False
            
        if not lead.get("phone"):
            print(f"[SKIP] No phone for {lead.get('name', 'Unknown')}")
            return False
        
        try:
            clean_phone = "".join(filter(str.isdigit, lead["phone"]))
            
            async with httpx.AsyncClient() as client:
                payload = {
                    "phone": clean_phone,
                    "message": lead["ai_analysis"],
                    "lead_name": lead["name"],
                    "category": lead["category"],
                    "website": lead.get("website", ""),
                    "source": "automated_scraper",
                    "timestamp": datetime.now().isoformat()
                }
                response = await client.post(self.n8n_webhook_url, json=payload, timeout=15.0)
                print(f"[N8N] Sent {lead['name']} -> {clean_phone} | Status: {response.status_code}")
                return response.status_code == 200
        except Exception as e:
            print(f"[ERROR] Failed to send to n8n: {e}")
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
        
        # Generate message
        if not details["website_snippet"] or details["website_snippet"] == "Could not load website.":
            details["ai_analysis"] = f"¡Hola! Estuve viendo el perfil de {details['name']} y me encantó el trabajo que realizan. Noté que aún no cuentan con un sitio web oficial, y hoy en día eso es clave para convertir seguidores en clientes.\n\nEn CLAVE.AI ayudamos a negocios a automatizar su crecimiento. Te invito a conocer nuestros servicios en https://claveai.lat y ver nuestro trabajo en https://www.instagram.com/claveai/."
        else:
            details["ai_analysis"] = f"¡Hola! Vi la web de {details['name']} y me pareció excelente. Sin embargo, noté algunas oportunidades para optimizar la conversión con IA.\n\nEn CLAVE.AI nos especializamos en potenciar negocios digitales. Puedes ver lo que hacemos en https://claveai.lat y seguirnos en https://www.instagram.com/claveai/."
        
        # Try AI analysis if available
        if HAS_ANALYZER and details["website_snippet"]:
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

                while leads_count < self.max_leads:
                    links = await page.locator('a[href*="/maps/place/"]').all()
                    
                    if not links:
                        await page.mouse.wheel(0, 3000)
                        await asyncio.sleep(2)
                        links = await page.locator('a[href*="/maps/place/"]').all()
                        if not links:
                            break

                    for link in links:
                        if leads_count >= self.max_leads:
                            break
                        
                        href = await link.get_attribute("href")
                        if href in processed_urls:
                            continue
                            
                        processed_urls.add(href)
                        
                        try:
                            await link.click()
                            await asyncio.sleep(random.randint(self.delay_min, self.delay_max) / 1000)
                            
                            lead = await self.extract_details(page, href)
                            self.leads.append(lead)
                            leads_count += 1
                            
                            print(f"[LEAD {leads_count}] {lead['name']} | Phone: {lead['phone'] or 'N/A'}")
                            
                            # Send to n8n immediately
                            if lead.get("phone"):
                                success = await self.send_to_n8n(lead)
                                if success:
                                    sent_count += 1
                                    
                        except Exception as e:
                            print(f"[ERROR] Extracting lead: {e}")
                            continue

                    # Scroll for more
                    await page.mouse.wheel(0, 2000)
                    await asyncio.sleep(2)
                    
                    # Check end of list
                    try:
                        if await page.locator('text="You\'ve reached the end of the list"').is_visible():
                            break
                    except:
                        pass

                print(f"\n{'='*60}")
                print(f"[DONE] Extracted: {leads_count} leads | Sent to WhatsApp: {sent_count}")
                print(f"{'='*60}\n")
                
            except Exception as e:
                print(f"[FATAL ERROR] {e}")
            finally:
                await browser.close()
                
        return self.leads


async def main():
    # Determine which URL to use based on day of week
    today = datetime.now()
    day_of_week = today.weekday()  # 0 = Monday, 6 = Sunday
    
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    # Check for command line override
    if len(sys.argv) > 1:
        try:
            day_of_week = int(sys.argv[1])
        except ValueError:
            pass
    
    url = DAILY_URLS.get(day_of_week, DAILY_URLS[0])
    
    print(f"\n🚀 CLAVE.AI Automated Lead Scraper")
    print(f"📅 Date: {today.strftime('%Y-%m-%d %H:%M')}")
    print(f"📆 Day: {day_names[day_of_week]}")
    print(f"🔗 URL: {url[:60]}...")
    print(f"📡 Webhook: {os.getenv('N8N_WEBHOOK_URL', 'NOT SET')[:50]}...")
    
    scraper = AutomatedScraper()
    leads = await scraper.scrape_url(url)
    
    print(f"\n✅ Completed! Total leads: {len(leads)}")
    

if __name__ == "__main__":
    asyncio.run(main())
