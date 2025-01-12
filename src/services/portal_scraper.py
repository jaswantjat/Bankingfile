from playwright.async_api import async_playwright
from typing import Optional, Dict
from loguru import logger
import json
import os
import json

class PortalScraper:
    def __init__(self):
        # Load portal configurations from JSON
        self.portals = self._load_portal_configs()
        
    def _load_portal_configs(self) -> Dict:
        """Load portal configurations from environment variable or default file"""
        portal_config = os.getenv('PORTAL_CONFIGS')
        if portal_config:
            return json.loads(portal_config)
            
        # Default to empty config if not specified
        return {}
        
    async def _init_browser(self):
        """Initialize playwright browser"""
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        return playwright, browser, context, page
        
    async def find_invoice_in_portal(self, vendor: str, amount: float, date: str) -> Optional[str]:
        """
        Try to find and download an invoice from the vendor's billing portal
        
        Args:
            vendor: Vendor name
            amount: Transaction amount
            date: Transaction date
        
        Returns:
            Optional[str]: Path to downloaded invoice if successful, None otherwise
        """
        # Check if we have portal config for this vendor
        portal_config = self.portals.get(vendor.lower())
        if not portal_config:
            logger.debug(f"No portal configuration found for vendor: {vendor}")
            return None
            
        try:
            playwright, browser, context, page = await self._init_browser()
            
            try:
                # Navigate to login page
                await page.goto(portal_config['login_url'])
                
                # Fill login form
                for field in portal_config['login_fields']:
                    await page.fill(field['selector'], os.getenv(field['env_var']))
                
                # Submit login form
                await page.click(portal_config['login_button'])
                await page.wait_for_load_state('networkidle')
                
                # Navigate to invoices/billing page
                if 'invoice_page_url' in portal_config:
                    await page.goto(portal_config['invoice_page_url'])
                elif 'invoice_page_link' in portal_config:
                    await page.click(portal_config['invoice_page_link'])
                    await page.wait_for_load_state('networkidle')
                
                # Search for invoice
                if 'search_form' in portal_config:
                    for field in portal_config['search_form']:
                        if field['type'] == 'date':
                            await page.fill(field['selector'], date)
                        elif field['type'] == 'amount':
                            await page.fill(field['selector'], str(amount))
                            
                    await page.click(portal_config['search_button'])
                    await page.wait_for_load_state('networkidle')
                
                # Check if invoice exists
                invoice_link = await page.query_selector(portal_config['invoice_link'])
                if not invoice_link:
                    logger.warning(f"No invoice found for {vendor} amount={amount} date={date}")
                    return None
                
                # Download invoice
                download_path = f"invoices/{vendor}_{date}_{amount}.pdf"
                async with page.expect_download() as download_info:
                    await invoice_link.click()
                download = await download_info.value
                
                # Save invoice
                await download.save_as(download_path)
                logger.info(f"Successfully downloaded invoice from {vendor}'s portal")
                return download_path
                
            finally:
                await context.close()
                await browser.close()
                await playwright.stop()
                
        except Exception as e:
            logger.error(f"Error accessing {vendor}'s portal: {str(e)}")
            return None
