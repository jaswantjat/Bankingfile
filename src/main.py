import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from datetime import datetime, timedelta
from loguru import logger
import sys
import os

from .models import Base, Transaction, Invoice, ProcessingError
from .scrapers.unionbank import UnionBankScraper
from .services.invoice_finder import InvoiceFinder
from .services.cloudcfo_uploader import CloudCFOUploader
from config.config import settings

# Configure logging
logger.remove()
logger.add(sys.stdout, level=settings.LOG_LEVEL)

# In production, log to file only if not running on Railway
if not os.getenv('RAILWAY_ENVIRONMENT'):
    logger.add("logs/transaction_manager.log", rotation="500 MB")

class TransactionManager:
    def __init__(self):
        self.engine = create_async_engine(settings.DATABASE_URL)
        self.SessionLocal = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
        self.scraper = UnionBankScraper()
        self.invoice_finder = InvoiceFinder()
        self.uploader = CloudCFOUploader()

    async def init_db(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def process_transaction(self, session: AsyncSession, transaction: Transaction):
        try:
            # Find invoice
            invoice = await self.invoice_finder.find_invoice(transaction)
            if not invoice:
                logger.warning(f"No invoice found for transaction {transaction.transaction_id}")
                transaction.status = 'failed'
                return
            
            # Upload to CloudCFO
            success = await self.uploader.upload_invoice(transaction, invoice)
            if success:
                transaction.status = 'uploaded'
                invoice.upload_status = 'uploaded'
            else:
                transaction.status = 'failed'
                invoice.upload_status = 'failed'
            
            session.add(invoice)
            
        except Exception as e:
            logger.error(f"Error processing transaction {transaction.transaction_id}: {str(e)}")
            transaction.status = 'failed'
            error = ProcessingError(
                transaction_id=transaction.id,
                error_type=type(e).__name__,
                error_message=str(e)
            )
            session.add(error)

    async def process_pending_transactions(self):
        async with self.SessionLocal() as session:
            # Get pending transactions
            result = await session.execute(
                select(Transaction).where(Transaction.status == 'pending')
            )
            pending_transactions = result.scalars().all()
            
            for transaction in pending_transactions:
                await self.process_transaction(session, transaction)
            
            await session.commit()

    async def check_new_transactions(self):
        try:
            # Get new transactions from UnionBank
            raw_transactions = await self.scraper.get_new_transactions()
            
            async with self.SessionLocal() as session:
                for raw_tx in raw_transactions:
                    # Check if transaction already exists
                    result = await session.execute(
                        select(Transaction).where(
                            Transaction.transaction_id == raw_tx['transaction_id']
                        )
                    )
                    existing = result.scalar_one_or_none()
                    
                    if not existing:
                        transaction = self.scraper._parse_transaction(raw_tx)
                        if transaction:
                            session.add(transaction)
                
                await session.commit()
                
        except Exception as e:
            logger.error(f"Error checking new transactions: {str(e)}")

    async def run(self):
        await self.init_db()
        
        while True:
            try:
                logger.info("Checking for new transactions...")
                await self.check_new_transactions()
                
                logger.info("Processing pending transactions...")
                await self.process_pending_transactions()
                
            except Exception as e:
                logger.error(f"Error in main loop: {str(e)}")
                
            finally:
                # Wait before next iteration
                await asyncio.sleep(900)  # 15 minutes

async def startup():
    try:
        manager = TransactionManager()
        await manager.run()
    except Exception as e:
        logger.error(f"Critical error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(startup())
