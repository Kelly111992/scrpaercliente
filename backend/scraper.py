import asyncio
import random
import uuid
import pandas as pd
from playwright.async_api import async_playwright
from analyzer import ai_analyzer
from sse_starlette.sse import EventSourceResponse
from typing import Dict, List, Optional
import json
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

class GMapsScraper:
    def __init__(self):
        self.jobs = {}
        self.n8n_webhook_url = os.getenv("N8N_WEBHOOK_URL")

    async def send_to_n8n(self, lead):
        print(f"[DEBUG] send_to_n8n called. Webhook URL: {self.n8n_webhook_url}")
        print(f"[DEBUG] Lead phone: '{lead.get('phone')}'")
        
        if not self.n8n_webhook_url:
            print("[DEBUG] No webhook URL configured, skipping")
            return
        
        if not lead.get("phone"):
            print("[DEBUG] No phone number in lead, skipping")
            return
        
        try:
            # Clean phone number (Evolution API expects digits, usually with country code)
            clean_phone = "".join(filter(str.isdigit, lead["phone"]))
            
            async with httpx.AsyncClient() as client:
                payload = {
                    "phone": clean_phone,
                    "message": lead["ai_analysis"],
                    "lead_name": lead["name"],
                    "category": lead["category"],
                    "website": lead["website"]
                }
                response = await client.post(self.n8n_webhook_url, json=payload, timeout=10.0)
                print(f"n8n Webhook response: {response.status_code}")
        except Exception as e:
            print(f"Error sending to n8n: {e}")

    async def scrape(self, job_id: str, url: str, mode: str, max_leads: int, delay_min: int, delay_max: int, extract_website: bool, extract_phone: bool, status_callback, auto_send_n8n: bool = False):
        self.jobs[job_id] = {"status": "running", "leads": [], "error": None}
        
        async with async_playwright() as p:
            # Set headless=False so the user can see if Google blocks with CAPTCHA
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            
            try:
                print(f"\n--- Starting Scrape Job: {job_id} ---")
                print(f"Mode: {mode}")
                print(f"Query: {url}")
                
                if mode == "instagram":
                    import urllib.parse
                    # Broad search for better results
                    search_query = urllib.parse.quote(f"site:instagram.com {url}")
                    google_url = f"https://www.google.com/search?q={search_query}"
                    
                    await status_callback({"type": "status", "message": f"Searching Google for Instagram profiles: {url}"})
                    await page.goto(google_url, wait_until="domcontentloaded", timeout=60000)
                    
                    leads_count = 0
                    while leads_count < max_leads:
                        # More robust result selectors for various Google layouts
                        result_selector = 'div.g, div.tF2Cxc, div.MjjYud, div.sr_item, div.SearchCard'
                        results = await page.locator(result_selector).all()
                        
                        if not results:
                            # Use a very broad search for any Instagram links to see if they exist
                            links = await page.locator('a[href*="instagram.com"]').all()
                            if links:
                                results = links # Treat direct links as results if containers aren't found
                        
                        if not results:
                            page_content = await page.content()
                            # Check for actual blocking elements, not just text in the page
                            is_captcha = await page.locator('iframe[src*="recaptcha"], #captcha-form, #recaptcha').count() > 0
                            
                            if is_captcha or "detecting unusual traffic" in page_content.lower():
                                await status_callback({"type": "status", "message": "⚠️ CAPTCHA detected! Please solve it in the browser window now..."})
                                try:
                                    # Wait for any of the result selectors to appear
                                    await page.wait_for_selector(result_selector, timeout=300000)
                                    await status_callback({"type": "status", "message": "CAPTCHA solved! Resuming search..."})
                                    results = await page.locator(result_selector).all()
                                except:
                                    await status_callback({"type": "error", "message": "Timeout: CAPTCHA was not solved in time."})
                                    return
                            else:
                                break
                            
                        if not results: break 
                            
                        for result in results:
                            if leads_count >= max_leads: break
                            
                            try:
                                # If it's a div.g, find the link inside
                                if await result.evaluate("node => node.tagName") == "DIV":
                                    link_elem = result.locator('a[href*="instagram.com"]').first
                                else:
                                    link_elem = result # It's already the link element

                                if not await link_elem.is_visible():
                                    continue
                                    
                                href = await link_elem.get_attribute("href")
                                if not href or "/p/" in href or "/reels/" in href or "/explore/" in href:
                                    continue 
                                
                                # Try to get title
                                try:
                                    title = await result.locator('h3').inner_text()
                                except:
                                    title = await link_elem.inner_text()
                                
                                # Clean username
                                try:
                                    username = href.split("instagram.com/")[1].split("/")[0].split("?")[0]
                                except:
                                    username = "User"

                                print(f"MATCH: Found profile @{username}")
                                
                                lead = {
                                    "name": title.split("•")[0].strip() if "•" in title else title,
                                    "category": "Instagram Profile",
                                    "address": "Instagram",
                                    "phone": "",
                                    "website": href,
                                    "rating": "N/A",
                                    "reviews_count": "0",
                                    "google_maps_url": href,
                                    "website_snippet": f"Instagram Profile: @{username}",
                                    "ai_analysis": f"¡Hola! Vi el perfil de {username} en Instagram y me encantó su contenido. Noté que podrían potenciar mucho más su marca con un sitio web automatizado que convierta seguidores en clientes las 24/7.\n\nEn CLAVE.AI nos especializamos en esto. ¡Te invito a conocer nuestros servicios en https://claveai.lat y ver nuestro trabajo en https://www.instagram.com/claveai/!"
                                }
                                
                                self.jobs[job_id]["leads"].append(lead)
                                leads_count += 1
                                await status_callback({"type": "lead", "data": lead, "count": leads_count})
                                
                                if auto_send_n8n and lead.get("phone"):
                                    await self.send_to_n8n(lead)
                                    
                                await asyncio.sleep(random.randint(delay_min, delay_max) / 1000)
                                
                            except Exception as e:
                                continue
                                
                        # Check for "Next" page
                        next_btn = page.locator('a#pnnext')
                        if await next_btn.is_visible():
                            await next_btn.click()
                            await asyncio.sleep(2)
                        else:
                            break
                            
                else:
                    # ORIGINAL GOOGLE MAPS FLOW
                    await status_callback({"type": "status", "message": f"Navigating to Maps: {url}"})
                    # Increased timeout and more lenient wait condition
                    await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                    await asyncio.sleep(5) # Wait a bit more for the elements to appear
                    
                    # Handle cookie consent if it appears
                    try:
                        consent_btn = page.locator('button[aria-label*="Accept"], button[aria-label*="Aceptar"]')
                        if await consent_btn.is_visible(timeout=5000):
                            await consent_btn.click()
                    except:
                        pass

                    leads_count = 0
                    processed_urls = set()

                    while leads_count < max_leads:
                        # Find business links
                        # Google Maps link selector for results
                        links = await page.locator('a[href*="/maps/place/"]').all()
                        
                        if not links:
                            await status_callback({"type": "info", "message": "No more results found or loading..."})
                            # Try scrolling to load more
                            await page.mouse.wheel(0, 5000)
                            await asyncio.sleep(2)
                            links = await page.locator('a[href*="/maps/place/"]').all()
                            if not links:
                                break

                        for link in links:
                            if leads_count >= max_leads:
                                break
                            
                            href = await link.get_attribute("href")
                            if href in processed_urls:
                                continue
                                
                            processed_urls.add(href)
                            
                            try:
                                # Click to open details
                                await link.click()
                                await asyncio.sleep(random.randint(delay_min, delay_max) / 1000)
                                
                                # Extract data from the detail panel
                                lead = await self.extract_details(page, href)
                                lead['google_maps_url'] = href
                                
                                # Improved Speech Template
                                if not lead["website_snippet"] or lead["website_snippet"] == "Could not load website.":
                                    lead["ai_analysis"] = f"¡Hola! Estuve viendo el perfil de {lead['name']} y me encantó el trabajo que realizan. Noté que aún no cuentan con un sitio web oficial, y hoy en día eso es clave para convertir seguidores en clientes.\n\nEn CLAVE.AI ayudamos a negocios a automatizar su crecimiento. Te invito a conocer nuestros servicios en https://claveai.lat y ver nuestro trabajo en https://www.instagram.com/claveai/."
                                else:
                                    lead["ai_analysis"] = f"¡Hola! Vi la web de {lead['name']} y me pareció excelente. Sin embargo, noté algunas oportunidades para optimizar la conversión con IA.\n\nEn CLAVE.AI nos especializamos en potenciar negocios digitales. Puedes ver lo que hacemos en https://claveai.lat y seguirnos en https://www.instagram.com/claveai/."

                                # AI Analysis call (Re-enabling for better personalization)
                                await asyncio.sleep(1)
                                try:
                                    analysis = await ai_analyzer.analyze_business(
                                        lead["name"], lead["category"], lead["website_snippet"]
                                    )
                                    if "Error" not in analysis:
                                        lead["ai_analysis"] = analysis
                                except:
                                    pass # Fallback to hardcoded template if AI fails

                                self.jobs[job_id]["leads"].append(lead)
                                leads_count += 1
                                
                                await status_callback({"type": "lead", "data": lead, "count": leads_count})
                                
                                if auto_send_n8n and lead.get("phone"):
                                    await self.send_to_n8n(lead)
                                
                            except Exception as e:
                                print(f"Error extracting lead: {e}")
                                continue

                        # Scroll to load more
                        await page.mouse.wheel(0, 3000)
                        await asyncio.sleep(2)
                        
                        # Check if we reached the end
                        end_text = await page.locator('text="You\'ve reached the end of the list"').is_visible()
                        if end_text:
                            break

                self.jobs[job_id]["status"] = "done"
                await status_callback({"type": "done", "job_id": job_id})

            except Exception as e:
                self.jobs[job_id]["status"] = "error"
                self.jobs[job_id]["error"] = str(e)
                await status_callback({"type": "error", "message": str(e)})
            finally:
                await browser.close()

    async def extract_details(self, page, url) -> Dict:
        # Selectors (Google Maps selectors change often, these are current common ones)
        # Using specific ARIA labels or data attributes is more robust
        
        name_selector = 'h1.DUwDvf'
        category_selector = 'button.DkEaL' # Often the first button with this class is category
        address_selector = 'button[data-item-id="address"]'
        phone_selector = 'button[data-item-id*="phone:tel:"]'
        website_selector = 'a[data-item-id="authority"]'
        rating_selector = 'div.F7kYV span.ceXN1' # Rating text
        reviews_selector = 'div.F7kYV span.Z4STNb' # Review count

        # Wait for the panel to load
        await page.wait_for_selector(name_selector, timeout=10000)

        details = {
            "name": await self.get_text(page, name_selector),
            "category": await self.get_text(page, category_selector),
            "address": await self.get_text(page, address_selector),
            "phone": await self.get_text(page, phone_selector),
            "website": await self.get_attr(page, website_selector, "href"),
            "rating": await self.get_text(page, 'span.rating-score'),
            "reviews_count": await self.get_text(page, 'button[aria-label*="reviews"]'),
            "website_snippet": "",
            "ai_analysis": "Pending..."
        }
        
        # New: Extract some text from the website if it exists
        if details["website"]:
            try:
                # Open a new tab to avoid losing the maps context
                site_page = await page.context.new_page()
                await site_page.goto(details["website"], wait_until="domcontentloaded", timeout=15000)
                # Get body text (first 2000 chars)
                details["website_snippet"] = await site_page.inner_text("body")
                details["website_snippet"] = details["website_snippet"][:2000]
                await site_page.close()
            except:
                details["website_snippet"] = "Could not load website."
                try: await site_page.close()
                except: pass
            
        return details
        if details["rating"] == "":
            # Try another way for rating
            try:
                rating_elem = await page.locator('span.ceXN1').first()
                details["rating"] = await rating_elem.inner_text() if await rating_elem.is_visible() else ""
            except: pass
            
        return details

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

scraper_instance = GMapsScraper()
