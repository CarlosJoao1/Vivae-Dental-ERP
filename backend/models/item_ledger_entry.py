"""
Item Ledger Entry Model - Tracks all item movements (consumption/output)
"""
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Index, Numeric
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from config.db import db
from models.base import BaseModel

class ItemLedgerEntry(BaseModel):
    __tablename__ = 'item_ledger_entries'
    
    # Primary fields
    posting_id = Column(UUID(as_uuid=True), nullable=False, default=uuid.uuid4, unique=True)
    tenant_id = Column(String(50), nullable=False)
    item_no = Column(String(50), nullable=False)
    description = Column(String(255))
    
    # Quantity & UOM
    quantity = Column(Numeric(15, 3), nullable=False)
    uom_code = Column(String(10), nullable=False)
    
    # Entry type & source
    entry_type = Column(String(20), nullable=False)  # 'Consumption' or 'Output'
    source_type = Column(String(50), nullable=False)  # 'ProductionOrder'
    source_id = Column(Integer)  # ID of source document
    production_order_no = Column(String(50))
    
    # Location & operation
    work_center_code = Column(String(50))
    operation_no = Column(Integer)
    
    # Costing (future)
    unit_cost = Column(Numeric(15, 4), default=0)
    total_cost = Column(Numeric(15, 4), default=0)
    
    # Posting info
    posting_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    posted_by = Column(String(100))
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))
    
    # Indexes for performance
    __table_args__ = (
        Index('ix_ile_tenant_item', 'tenant_id', 'item_no'),
        Index('ix_ile_tenant_posting', 'tenant_id', 'posting_id'),
        Index('ix_ile_tenant_order', 'tenant_id', 'production_order_no'),
        Index('ix_ile_posting_date', 'posting_date'),
        Index('ix_ile_entry_type', 'entry_type'),
    )
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'posting_id': str(self.posting_id),
            'tenant_id': self.tenant_id,
            'item_no': self.item_no,
            'description': self.description,
            'quantity': float(self.quantity) if self.quantity else 0,
            'uom_code': self.uom_code,
            'entry_type': self.entry_type,
            'source_type': self.source_type,
            'source_id': self.source_id,
            'production_order_no': self.production_order_no,
            'work_center_code': self.work_center_code,
            'operation_no': self.operation_no,
            'unit_cost': float(self.unit_cost) if self.unit_cost else 0,
            'total_cost': float(self.total_cost) if self.total_cost else 0,
            'posting_date': self.posting_date.isoformat() if self.posting_date else None,
            'posted_by': self.posted_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'created_by': self.created_by
        }
