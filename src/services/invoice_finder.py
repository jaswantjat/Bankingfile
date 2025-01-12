import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from slack_sdk import WebClient
from datetime import datetime, timedelta
from loguru import logger
from typing import Optional
import os
from .portal_scraper import PortalScraper
from ..models import Transaction, Invoice
from config.config import settings
import aiohttp
import base64
from dateutil.parser import parse

class InvoiceFinder:
    def __init__(self):
        self._setup_gmail_client()
        self._setup_slack_client()
        self._setup_drive_client()
        self.portal_scraper = PortalScraper()
        
    def _setup_gmail_client(self):
        """Setup Gmail API client"""
        creds = Credentials.from_authorized_user_info(
            json.loads(os.getenv('GMAIL_API_KEY'))
        )
        self.gmail = build('gmail', 'v1', credentials=creds)
        
    def _setup_slack_client(self):
        """Setup Slack client"""
        self.slack = WebClient(token=os.getenv('SLACK_API_KEY'))
        
    def _setup_drive_client(self):
        """Setup Google Drive client"""
        creds = Credentials.from_authorized_user_info(
            json.loads(os.getenv('DRIVE_API_KEY'))
        )
        self.drive = build('drive', 'v3', credentials=creds)
    
    async def find_invoice(self, transaction: Transaction) -> Optional[Invoice]:
        """
        Find invoice for a transaction by searching Gmail, Slack, Drive and vendor portals
        
        Returns:
            Optional[Invoice]: Invoice object if found, None otherwise
        """
        # Search in Gmail
        invoice_path = await self._search_gmail(
            transaction.vendor,
            transaction.amount,
            transaction.date
        )
        if invoice_path:
            return Invoice(
                transaction_id=transaction.id,
                file_path=invoice_path,
                source='gmail'
            )
            
        # Search in Slack
        invoice_path = await self._search_slack(
            transaction.vendor,
            transaction.amount,
            transaction.date
        )
        if invoice_path:
            return Invoice(
                transaction_id=transaction.id,
                file_path=invoice_path,
                source='slack'
            )
            
        # Search in Drive
        invoice_path = await self._search_drive(
            transaction.vendor,
            transaction.amount,
            transaction.date
        )
        if invoice_path:
            return Invoice(
                transaction_id=transaction.id,
                file_path=invoice_path,
                source='drive'
            )
            
        # Fallback: Try vendor's billing portal
        invoice_path = await self.portal_scraper.find_invoice_in_portal(
            transaction.vendor,
            transaction.amount,
            transaction.date
        )
        if invoice_path:
            return Invoice(
                transaction_id=transaction.id,
                file_path=invoice_path,
                source='portal'
            )
            
        logger.warning(f"No invoice found for transaction {transaction.id}")
        return None
        
    async def _search_gmail(self, vendor: str, amount: float, date: str) -> Optional[str]:
        """Search for invoice in Gmail"""
        try:
            # Build search query
            query = f"from:{vendor} invoice amount:{amount} after:{date}"
            
            # Search emails
            results = self.gmail.users().messages().list(
                userId='me',
                q=query
            ).execute()
            
            messages = results.get('messages', [])
            if not messages:
                return None
                
            # Get first message with attachment
            for msg in messages:
                message = self.gmail.users().messages().get(
                    userId='me',
                    id=msg['id']
                ).execute()
                
                if 'parts' in message['payload']:
                    for part in message['payload']['parts']:
                        if part['filename'].endswith('.pdf'):
                            attachment = self.gmail.users().messages().attachments().get(
                                userId='me',
                                messageId=msg['id'],
                                id=part['body']['attachmentId']
                            ).execute()
                            
                            # Save attachment
                            file_path = f"invoices/gmail_{vendor}_{date}_{amount}.pdf"
                            with open(file_path, 'wb') as f:
                                f.write(base64.urlsafe_b64decode(attachment['data']))
                            return file_path
                            
            return None
            
        except Exception as e:
            logger.error(f"Error searching Gmail: {str(e)}")
            return None
            
    async def _search_slack(self, vendor: str, amount: float, date: str) -> Optional[str]:
        """Search for invoice in Slack"""
        try:
            # Build search query
            query = f"from:{vendor} invoice amount:{amount} after:{date}"
            
            # Search messages
            result = self.slack.search_messages(
                query=query,
                sort='timestamp',
                sort_dir='desc'
            )
            
            if not result['messages']['matches']:
                return None
                
            # Look for file attachments
            for message in result['messages']['matches']:
                if 'files' in message:
                    for file in message['files']:
                        if file['name'].endswith('.pdf'):
                            # Download file
                            file_path = f"invoices/slack_{vendor}_{date}_{amount}.pdf"
                            async with aiohttp.ClientSession() as session:
                                async with session.get(file['url_private'], headers={
                                    'Authorization': f'Bearer {settings.SLACK_API_KEY}'
                                }) as response:
                                    if response.status == 200:
                                        with open(file_path, 'wb') as f:
                                            f.write(await response.read())
                                        return file_path
                            
            return None
            
        except Exception as e:
            logger.error(f"Error searching Slack: {str(e)}")
            return None
            
    async def _search_drive(self, vendor: str, amount: float, date: str) -> Optional[str]:
        """Search for invoice in Google Drive"""
        try:
            # Build search query
            query = f"fullText contains '{vendor}' and fullText contains 'invoice' and fullText contains '{amount}'"
            
            # Search files
            results = self.drive.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)',
                orderBy='modifiedTime desc'
            ).execute()
            
            files = results.get('files', [])
            if not files:
                return None
                
            # Download first matching file
            file_id = files[0]['id']
            file_path = f"invoices/drive_{vendor}_{date}_{amount}.pdf"
            
            request = self.drive.files().get_media(fileId=file_id)
            with open(file_path, 'wb') as f:
                f.write(request.execute())
            return file_path
            
        except Exception as e:
            logger.error(f"Error searching Drive: {str(e)}")
            return None
