import asyncio
from datetime import datetime, timedelta
from loguru import logger
import sys
from src.scrapers.unionbank import UnionBankScraper
from src.services.invoice_finder import InvoiceFinder
from src.services.cloudcfo_uploader import CloudCFOUploader
from src.models import Transaction, Invoice, Base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from config.config import settings
import os

# Configure logging to show everything
logger.remove()
logger.add(sys.stdout, level="INFO", format="<green>{time:HH:mm:ss}</green> | {level} | <blue>{message}</blue>")

class TransactionManagerDemo:
    def __init__(self):
        self.engine = create_async_engine(settings.DATABASE_URL)
        self.SessionLocal = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
        self.scraper = UnionBankScraper()
        self.invoice_finder = InvoiceFinder()
        self.uploader = CloudCFOUploader()

    async def init_db(self):
        """Initialize the database"""
        logger.info("Initializing database...")
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)  # Clean start for demo
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized!")

    async def demo_transaction_fetch(self):
        """Demonstrate fetching transactions from UnionBank"""
        logger.info("\n=== Step 1: Fetching Transactions from UnionBank ===")
        logger.info("Logging into UnionBank...")
        await self.scraper.login()
        logger.info("Successfully logged in!")

        logger.info("Fetching recent transactions...")
        transactions = await self.scraper.get_new_transactions()
        logger.info(f"Found {len(transactions)} new transactions!")

        async with self.SessionLocal() as session:
            for tx_data in transactions:
                tx = Transaction(
                    transaction_id=tx_data['transaction_id'],
                    date=tx_data['date'],
                    amount=tx_data['amount'],
                    vendor=tx_data['vendor'],
                    description=tx_data['description'],
                    status='pending'
                )
                session.add(tx)
            await session.commit()

        return transactions

    async def demo_invoice_search(self, transaction):
        """Demonstrate invoice search across platforms"""
        logger.info(f"\n=== Step 2: Finding Invoice for Transaction {transaction['transaction_id']} ===")
        
        # Search in Gmail
        logger.info("Searching in Gmail...")
        invoice_path = await self.invoice_finder._search_gmail(
            transaction['vendor'],
            transaction['amount'],
            transaction['date'].strftime('%Y-%m-%d')
        )
        if invoice_path:
            logger.info(f"Found invoice in Gmail: {invoice_path}")
            return invoice_path

        # Search in Slack
        logger.info("Searching in Slack...")
        invoice_path = await self.invoice_finder._search_slack(
            transaction['vendor'],
            transaction['amount'],
            transaction['date'].strftime('%Y-%m-%d')
        )
        if invoice_path:
            logger.info(f"Found invoice in Slack: {invoice_path}")
            return invoice_path

        # Search in Drive
        logger.info("Searching in Google Drive...")
        invoice_path = await self.invoice_finder._search_drive(
            transaction['vendor'],
            transaction['amount'],
            transaction['date'].strftime('%Y-%m-%d')
        )
        if invoice_path:
            logger.info(f"Found invoice in Google Drive: {invoice_path}")
            return invoice_path

        # Try vendor portal
        logger.info("Trying vendor portal...")
        invoice_path = await self.invoice_finder.portal_scraper.find_invoice_in_portal(
            transaction['vendor'],
            transaction['amount'],
            transaction['date'].strftime('%Y-%m-%d')
        )
        if invoice_path:
            logger.info(f"Found invoice in vendor portal: {invoice_path}")
            return invoice_path

        logger.warning("No invoice found!")
        return None

    async def demo_cloudcfo_upload(self, transaction, invoice_path):
        """Demonstrate uploading to CloudCFO"""
        if not invoice_path:
            logger.warning("\n=== Step 3: Skipping CloudCFO Upload (No Invoice) ===")
            return

        logger.info("\n=== Step 3: Uploading to CloudCFO ===")
        logger.info("Logging into CloudCFO...")
        await self.uploader.login()
        logger.info("Successfully logged in!")

        logger.info(f"Uploading invoice for transaction {transaction['transaction_id']}...")
        success = await self.uploader.upload_invoice(transaction, invoice_path)
        
        if success:
            logger.info("Successfully uploaded invoice to CloudCFO!")
        else:
            logger.error("Failed to upload invoice to CloudCFO")

    async def run_demo(self):
        """Run the complete demo"""
        logger.info("Starting Transaction Manager Demo...")
        
        # Initialize database
        await self.init_db()

        # Fetch transactions
        transactions = await self.demo_transaction_fetch()

        # Process each transaction
        for transaction in transactions[:3]:  # Demo with first 3 transactions
            logger.info(f"\nProcessing transaction: {transaction['transaction_id']}")
            logger.info(f"Amount: ${transaction['amount']}")
            logger.info(f"Vendor: {transaction['vendor']}")
            logger.info(f"Date: {transaction['date']}")

            # Find invoice
            invoice_path = await self.demo_invoice_search(transaction)

            # Upload to CloudCFO
            await self.demo_cloudcfo_upload(transaction, invoice_path)

        logger.info("\n=== Demo Complete! ===")

async def main():
    demo = TransactionManagerDemo()
    await demo.run_demo()

if __name__ == "__main__":
    asyncio.run(main())
