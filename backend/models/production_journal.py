"""
Production Journal Model - Header for consumption/output/capacity postings
"""
from sqlalchemy import Column, String, Integer, DateTime, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from config.db import db
from models.base import BaseModel

class ProductionJournal(BaseModel):
    __tablename__ = 'production_journals'
    
    # Primary fields
    posting_id = Column(UUID(as_uuid=True), nullable=False, default=uuid.uuid4, unique=True)
    tenant_id = Column(String(50), nullable=False)
    
    # Journal identification
    journal_type = Column(String(20), nullable=False)  # 'Consumption', 'Output', 'Capacity'
    production_order_no = Column(String(50), nullable=False)
    
    # Posting info
    posting_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    posted_by = Column(String(100))
    notes = Column(Text)
    
    # Status tracking
    status = Column(String(20), default='Posted')  # 'Posted', 'Reversed'
    reversed_by = Column(String(100))
    reversed_at = Column(DateTime)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))
    
    # Indexes for performance
    __table_args__ = (
        Index('ix_pj_tenant_posting', 'tenant_id', 'posting_id'),
        Index('ix_pj_tenant_order', 'tenant_id', 'production_order_no'),
        Index('ix_pj_posting_date', 'posting_date'),
        Index('ix_pj_journal_type', 'journal_type'),
    )
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'posting_id': str(self.posting_id),
            'tenant_id': self.tenant_id,
            'journal_type': self.journal_type,
            'production_order_no': self.production_order_no,
            'posting_date': self.posting_date.isoformat() if self.posting_date else None,
            'posted_by': self.posted_by,
            'notes': self.notes,
            'status': self.status,
            'reversed_by': self.reversed_by,
            'reversed_at': self.reversed_at.isoformat() if self.reversed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'created_by': self.created_by
        }
