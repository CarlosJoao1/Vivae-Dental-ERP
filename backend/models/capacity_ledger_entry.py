"""
Capacity Ledger Entry Model - Tracks work center/machine capacity usage
"""
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Index, Numeric
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from config.db import db
from models.base import BaseModel

class CapacityLedgerEntry(BaseModel):
    __tablename__ = 'capacity_ledger_entries'
    
    # Primary fields
    posting_id = Column(UUID(as_uuid=True), nullable=False, default=uuid.uuid4, unique=True)
    tenant_id = Column(String(50), nullable=False)
    
    # Resource identification
    work_center_code = Column(String(50), nullable=False)
    machine_center_code = Column(String(50))
    
    # Operation reference
    operation_no = Column(Integer, nullable=False)
    production_order_no = Column(String(50), nullable=False)
    item_no = Column(String(50))
    
    # Time tracking (in minutes)
    setup_time = Column(Numeric(15, 2), default=0)
    run_time = Column(Numeric(15, 2), default=0)
    stop_time = Column(Numeric(15, 2), default=0)  # Downtime
    scrap_time = Column(Numeric(15, 2), default=0)  # Time lost to scrap
    
    # Quantity processed
    quantity = Column(Numeric(15, 3), default=0)
    scrap_quantity = Column(Numeric(15, 3), default=0)
    
    # Costing (future)
    unit_cost = Column(Numeric(15, 4), default=0)
    total_cost = Column(Numeric(15, 4), default=0)
    
    # Operator info
    operator_id = Column(String(50))
    operator_name = Column(String(100))
    
    # Posting info
    posting_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    posted_by = Column(String(100))
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))
    
    # Indexes for performance
    __table_args__ = (
        Index('ix_cle_tenant_wc', 'tenant_id', 'work_center_code'),
        Index('ix_cle_tenant_posting', 'tenant_id', 'posting_id'),
        Index('ix_cle_tenant_order', 'tenant_id', 'production_order_no'),
        Index('ix_cle_posting_date', 'posting_date'),
        Index('ix_cle_operator', 'operator_id'),
    )
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'posting_id': str(self.posting_id),
            'tenant_id': self.tenant_id,
            'work_center_code': self.work_center_code,
            'machine_center_code': self.machine_center_code,
            'operation_no': self.operation_no,
            'production_order_no': self.production_order_no,
            'item_no': self.item_no,
            'setup_time': float(self.setup_time) if self.setup_time else 0,
            'run_time': float(self.run_time) if self.run_time else 0,
            'stop_time': float(self.stop_time) if self.stop_time else 0,
            'scrap_time': float(self.scrap_time) if self.scrap_time else 0,
            'quantity': float(self.quantity) if self.quantity else 0,
            'scrap_quantity': float(self.scrap_quantity) if self.scrap_quantity else 0,
            'unit_cost': float(self.unit_cost) if self.unit_cost else 0,
            'total_cost': float(self.total_cost) if self.total_cost else 0,
            'operator_id': self.operator_id,
            'operator_name': self.operator_name,
            'posting_date': self.posting_date.isoformat() if self.posting_date else None,
            'posted_by': self.posted_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'created_by': self.created_by
        }
