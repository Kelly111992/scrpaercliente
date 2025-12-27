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

class GMapsScraper:
    def __init__(self):
        self.jobs = {}

    async def scrape(self, job_id: str, url: str, max_leads: int, delay_min: int, delay_max: int, extract_website: bool, extract_phone: bool, status_callback):
        self.jobs[job_id] = {"status": "running", "leads": [], "error": None}
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False) # Headless=False to see what's happening if needed, or True for production
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            
            try:
                await status_callback({"type": "status", "message": f"Navigating to {url}"})
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
                            
                            # New: Local Speech Template (AI disabled for stability)
                            if not lead["website_snippet"] or lead["website_snippet"] == "Could not load website.":
                                lead["ai_analysis"] = f"¡Hola! Estuve viendo el perfil de {lead['name']} y me encantó lo que hacen. Noté que aún no cuentan con un sitio web oficial; hoy en día no tener presencia digital es casi ser invisible. En CLAVE.AI nos especializamos en transformar negocios con sitios web inteligentes y automatización con IA para que vendas incluso mientras descansas. Te invito a ver nuestro trabajo en https://www.instagram.com/claveai y si te interesa potenciar {lead['name']}, ¡aquí estoy para ayudarte!"
                            else:
                                lead["ai_analysis"] = "Este negocio ya cuenta con sitio web. Concentrándonos en prospección de nuevos sitios..."

                            # AI Analysis call disabled as per user request
                            # await asyncio.sleep(2)
                            # await status_callback({"type": "status", "message": f"Analyzing {lead['name']} with AI..."})
                            # lead["ai_analysis"] = await ai_analyzer.analyze_business(
                            #     lead["name"], lead["category"], lead["website_snippet"]
                            # )

                            self.jobs[job_id]["leads"].append(lead)
                            leads_count += 1
                            
                            await status_callback({"type": "lead", "data": lead, "count": leads_count})
                            
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
