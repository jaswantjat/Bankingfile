from playwright.async_api import async_playwright
import asyncio
import os
from dotenv import load_dotenv

async def verify_unionbank():
    load_dotenv()
    
    url = os.getenv('UNIONBANK_URL')
    username = os.getenv('UNIONBANK_USERNAME')
    password = os.getenv('UNIONBANK_PASSWORD')
    
    print("\nTesting UnionBank credentials...")
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        try:
            await page.goto(url)
            await page.fill('input[name="username"]', username)
            await page.fill('input[name="password"]', password)
            await page.click('button[type="submit"]')
            await page.wait_for_load_state('networkidle')
            
            # Check for error messages
            error = await page.locator('.error-message').count()
            if error > 0:
                print("❌ UnionBank login failed. Please check your credentials.")
            else:
                print("✅ UnionBank login successful!")
                
        except Exception as e:
            print(f"❌ UnionBank error: {str(e)}")
        
        await browser.close()

async def verify_cloudcfo():
    load_dotenv()
    
    url = os.getenv('CLOUDCFO_URL')
    username = os.getenv('CLOUDCFO_USERNAME')
    password = os.getenv('CLOUDCFO_PASSWORD')
    
    print("\nTesting CloudCFO credentials...")
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        try:
            await page.goto(url)
            await page.fill('input[name="username"]', username)
            await page.fill('input[name="password"]', password)
            await page.click('button[type="submit"]')
            await page.wait_for_load_state('networkidle')
            
            # Check for error messages
            error = await page.locator('.error-message').count()
            if error > 0:
                print("❌ CloudCFO login failed. Please check your credentials.")
            else:
                print("✅ CloudCFO login successful!")
                
        except Exception as e:
            print(f"❌ CloudCFO error: {str(e)}")
        
        await browser.close()

async def main():
    print("Verifying web credentials...")
    await verify_unionbank()
    await verify_cloudcfo()
    
    print("\nIf all tests passed, your credentials are correct!")
    print("If any tests failed, please update your credentials in the .env file.")

if __name__ == "__main__":
    asyncio.run(main())
