from playwright.async_api import async_playwright
from datetime import datetime
from typing import List, Dict, Optional
from ..models import Transaction
from config.config import settings
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

class UnionBankScraper:
    def __init__(self):
        self.url = settings.UNIONBANK_URL
        self.username = settings.UNIONBANK_USERNAME
        self.password = settings.UNIONBANK_PASSWORD

    async def _init_browser(self):
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        return playwright, browser, context, page

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def login(self, page):
        try:
            await page.goto(self.url)
            await page.fill('input[name="username"]', self.username)
            await page.fill('input[name="password"]', self.password)
            await page.click('button[type="submit"]')
            await page.wait_for_load_state('networkidle')
            
            # Verify login success
            if await page.locator('.error-message').count() > 0:
                raise Exception("Login failed")
                
        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            raise

    async def extract_transactions(self, page) -> List[Dict]:
        transactions = []
        try:
            # Navigate to transactions page
            await page.click('text=Transactions')
            await page.wait_for_load_state('networkidle')
            
            # Extract transaction data
            rows = await page.query_selector_all('table tr')
            for row in rows[1:]:  # Skip header row
                columns = await row.query_selector_all('td')
                
                date_text = await columns[0].inner_text()
                amount_text = await columns[1].inner_text()
                vendor_text = await columns[2].inner_text()
                
                transaction = {
                    'date': datetime.strptime(date_text.strip(), '%Y-%m-%d'),
                    'amount': float(amount_text.strip().replace('$', '').replace(',', '')),
                    'vendor': vendor_text.strip(),
                    'transaction_id': await columns[3].inner_text()  # Assuming there's a transaction ID column
                }
                transactions.append(transaction)
                
        except Exception as e:
            logger.error(f"Failed to extract transactions: {str(e)}")
            raise
            
        return transactions

    async def get_new_transactions(self) -> List[Dict]:
        playwright, browser, context, page = await self._init_browser()
        
        try:
            await self.login(page)
            transactions = await self.extract_transactions(page)
            return transactions
            
        finally:
            await context.close()
            await browser.close()
            await playwright.stop()

    @staticmethod
    def _parse_transaction(raw_transaction: Dict) -> Optional[Transaction]:
        try:
            return Transaction(
                transaction_id=raw_transaction['transaction_id'],
                amount=raw_transaction['amount'],
                date=raw_transaction['date'],
                vendor=raw_transaction['vendor'],
                status='pending'
            )
        except Exception as e:
            logger.error(f"Failed to parse transaction: {str(e)}")
            return None
