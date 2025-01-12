from sqlalchemy import Column, Integer, String, DateTime, Numeric, Enum, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Transaction(Base):
    __tablename__ = 'transactions'
    
    id = Column(Integer, primary_key=True)
    transaction_id = Column(String, unique=True, nullable=False)
    amount = Column(Numeric, nullable=False)
    date = Column(DateTime, nullable=False)
    vendor = Column(String, nullable=False)
    status = Column(Enum('pending', 'matched', 'uploaded', 'failed', name='transaction_status'), default='pending')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    invoice = relationship("Invoice", back_populates="transaction", uselist=False)

class Invoice(Base):
    __tablename__ = 'invoices'
    
    id = Column(Integer, primary_key=True)
    transaction_id = Column(Integer, ForeignKey('transactions.id'), unique=True)
    file_path = Column(String, nullable=False)
    source = Column(Enum('gmail', 'slack', 'drive', 'portal', name='invoice_source'))
    upload_status = Column(Enum('pending', 'uploaded', 'failed', name='upload_status'), default='pending')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    transaction = relationship("Transaction", back_populates="invoice")

class ProcessingError(Base):
    __tablename__ = 'processing_errors'
    
    id = Column(Integer, primary_key=True)
    transaction_id = Column(Integer, ForeignKey('transactions.id'))
    error_type = Column(String, nullable=False)
    error_message = Column(String)
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    transaction = relationship("Transaction")
