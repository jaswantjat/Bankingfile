from typing import Optional, List
from datetime import datetime, timedelta
from ..models import Transaction, Invoice
from config.config import settings
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from slack_sdk import WebClient
from loguru import logger
import os
import aiohttp
import base64
from dateutil.parser import parse

class InvoiceFinder:
    def __init__(self):
        self.gmail_creds = Credentials.from_authorized_user_info(info=settings.GMAIL_API_KEY)
        self.slack_client = WebClient(token=settings.SLACK_API_KEY)
        self.drive_service = build('drive', 'v3', credentials=self.gmail_creds)

    async def search_gmail(self, transaction: Transaction) -> Optional[str]:
        try:
            service = build('gmail', 'v1', credentials=self.gmail_creds)
            
            # Create search query
            search_date = transaction.date.strftime('%Y/%m/%d')
            amount_str = f"${transaction.amount}"
            query = f"from:{transaction.vendor} {amount_str} after:{search_date}"
            
            results = service.users().messages().list(userId='me', q=query).execute()
            messages = results.get('messages', [])
            
            for message in messages:
                msg = service.users().messages().get(userId='me', id=message['id']).execute()
                
                # Check for attachments
                if 'parts' in msg['payload']:
                    for part in msg['payload']['parts']:
                        if part['filename'].lower().endswith(('.pdf', '.jpg', '.png')):
                            attachment = service.users().messages().attachments().get(
                                userId='me', messageId=message['id'], id=part['body']['attachmentId']
                            ).execute()
                            
                            # Save attachment
                            file_data = base64.urlsafe_b64decode(attachment['data'])
                            file_path = f"invoices/{transaction.transaction_id}_{part['filename']}"
                            os.makedirs(os.path.dirname(file_path), exist_ok=True)
                            
                            with open(file_path, 'wb') as f:
                                f.write(file_data)
                            
                            return file_path
                            
        except Exception as e:
            logger.error(f"Gmail search failed for transaction {transaction.transaction_id}: {str(e)}")
            return None

    async def search_slack(self, transaction: Transaction) -> Optional[str]:
        try:
            # Search messages around transaction date
            start_time = transaction.date - timedelta(days=7)
            end_time = transaction.date + timedelta(days=7)
            
            result = self.slack_client.search_files(
                query=f"from:{transaction.vendor} {transaction.amount}",
                count=10,
                page=1
            )
            
            for file in result['files']['matches']:
                file_date = parse(file['created'])
                if start_time <= file_date <= end_time:
                    # Download file
                    async with aiohttp.ClientSession() as session:
                        async with session.get(file['url_private'], headers={
                            'Authorization': f'Bearer {settings.SLACK_API_KEY}'
                        }) as response:
                            if response.status == 200:
                                file_path = f"invoices/{transaction.transaction_id}_{file['name']}"
                                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                                
                                with open(file_path, 'wb') as f:
                                    f.write(await response.read())
                                
                                return file_path
                                
        except Exception as e:
            logger.error(f"Slack search failed for transaction {transaction.transaction_id}: {str(e)}")
            return None

    async def search_drive(self, transaction: Transaction) -> Optional[str]:
        try:
            # Search for files in Google Drive
            query = f"fullText contains '{transaction.vendor}' and fullText contains '{transaction.amount}'"
            results = self.drive_service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name, createdTime)',
                pageSize=10
            ).execute()
            
            for file in results.get('files', []):
                file_date = parse(file['createdTime'])
                if abs((file_date - transaction.date).days) <= 7:
                    # Download file
                    file_path = f"invoices/{transaction.transaction_id}_{file['name']}"
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    
                    request = self.drive_service.files().get_media(fileId=file['id'])
                    with open(file_path, 'wb') as f:
                        downloader = MediaIoBaseDownload(f, request)
                        done = False
                        while done is False:
                            status, done = downloader.next_chunk()
                    
                    return file_path
                    
        except Exception as e:
            logger.error(f"Drive search failed for transaction {transaction.transaction_id}: {str(e)}")
            return None

    async def find_invoice(self, transaction: Transaction) -> Optional[Invoice]:
        """Search for invoice across multiple platforms"""
        
        # Try Gmail first
        if file_path := await self.search_gmail(transaction):
            return Invoice(
                transaction_id=transaction.id,
                file_path=file_path,
                source='gmail'
            )
            
        # Try Slack
        if file_path := await self.search_slack(transaction):
            return Invoice(
                transaction_id=transaction.id,
                file_path=file_path,
                source='slack'
            )
            
        # Try Google Drive
        if file_path := await self.search_drive(transaction):
            return Invoice(
                transaction_id=transaction.id,
                file_path=file_path,
                source='drive'
            )
            
        return None
