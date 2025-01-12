from playwright.async_api import async_playwright
from ..models import Transaction, Invoice
from config.config import settings
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

class CloudCFOUploader:
    def __init__(self):
        self.url = settings.CLOUDCFO_URL
        self.username = settings.CLOUDCFO_USERNAME
        self.password = settings.CLOUDCFO_PASSWORD

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
            logger.error(f"CloudCFO login failed: {str(e)}")
            raise

    async def upload_invoice(self, transaction: Transaction, invoice: Invoice) -> bool:
        playwright, browser, context, page = await self._init_browser()
        
        try:
            await self.login(page)
            
            # Navigate to upload page
            await page.click('text=Upload Invoice')
            await page.wait_for_load_state('networkidle')
            
            # Fill in transaction details
            await page.fill('input[name="amount"]', str(transaction.amount))
            await page.fill('input[name="date"]', transaction.date.strftime('%Y-%m-%d'))
            await page.fill('input[name="vendor"]', transaction.vendor)
            
            # Upload file
            input_file = await page.query_selector('input[type="file"]')
            await input_file.set_input_files(invoice.file_path)
            
            # Submit form
            await page.click('button[type="submit"]')
            await page.wait_for_load_state('networkidle')
            
            # Verify upload success
            success_message = await page.locator('.success-message').count() > 0
            if not success_message:
                raise Exception("Upload verification failed")
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to upload invoice for transaction {transaction.transaction_id}: {str(e)}")
            return False
            
        finally:
            await context.close()
            await browser.close()
            await playwright.stop()
