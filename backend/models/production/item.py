# backend/models/production/item.py
"""
Item Model (NAV/BC-style)
Items/Articles for inventory, production, and purchasing
"""
from mongoengine import (
    Document, StringField, IntField, FloatField, DateTimeField, 
    ReferenceField, DictField, BooleanField
)
from datetime import datetime
from models.laboratory import Laboratory


class Item(Document):
    """
    Item (Article) - NAV/BC style
    
    Represents items that can be:
    - Manufactured (finished goods with BOM)
    - Purchased (raw materials/components)
    - Both (semi-finished goods)
    """
    meta = {
        'collection': 'items',
        'indexes': [
            {'fields': ['tenant_id', 'item_no'], 'unique': True},  # PK logic
            'tenant_id',
            'item_no',
            'item_type',
            'status',
        ]
    }
    
    # Multi-tenancy
    tenant_id = ReferenceField(Laboratory, required=True, db_field='tenant_id')
    
    # Core identification
    item_no = StringField(required=True, max_length=20)  # e.g., "FG-CHAIR-001"
    description = StringField(required=True, max_length=100)
    description_2 = StringField(max_length=100)  # Additional description
    
    # Item classification
    item_type = StringField(
        required=True, 
        choices=['manufactured', 'purchased', 'both'],
        default='manufactured'
    )
    
    # Unit of Measure
    base_uom = StringField(required=True, max_length=10)  # Reference to UOM code
    
    # Purchasing data
    default_supplier_id = StringField(max_length=50)  # Reference to Supplier
    lead_time_days = IntField(min_value=0, default=0)  # Lead time for procurement/production
    safety_stock_qty = FloatField(min_value=0, default=0)  # Safety stock level
    reorder_point = FloatField(min_value=0)  # When to reorder
    reorder_quantity = FloatField(min_value=0)  # How much to reorder
    
    # Costing (for future use)
    unit_cost = FloatField(min_value=0)  # Standard/Average cost
    costing_method = StringField(
        choices=['standard', 'average', 'fifo'], 
        default='standard'
    )
    
    # Status
    status = StringField(
        required=True,
        choices=['Active', 'Blocked'],
        default='Active'
    )
    
    # Posting groups (for GL integration - optional for MVP)
    posting_groups = DictField()  # { gen_prod_posting_group, vat_prod_posting_group }
    
    # Flags
    critical_item = BooleanField(default=False)  # Mark as critical for MRP
    phantom_bom = BooleanField(default=False)  # BOM components explode through
    
    # Audit fields
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    created_by = StringField(max_length=50)
    updated_by = StringField(max_length=50)
    
    def save(self, *args, **kwargs):
        """Override save to update timestamp"""
        self.updated_at = datetime.utcnow()
        return super().save(*args, **kwargs)
    
    def to_dict(self):
        """Serialize to dictionary"""
        return {
            'id': str(self.id),
            'tenant_id': str(self.tenant_id.id),
            'item_no': self.item_no,
            'description': self.description,
            'description_2': self.description_2,
            'item_type': self.item_type,
            'base_uom': self.base_uom,
            'default_supplier_id': self.default_supplier_id,
            'lead_time_days': self.lead_time_days,
            'safety_stock_qty': self.safety_stock_qty,
            'reorder_point': self.reorder_point,
            'reorder_quantity': self.reorder_quantity,
            'unit_cost': self.unit_cost,
            'costing_method': self.costing_method,
            'status': self.status,
            'posting_groups': self.posting_groups,
            'critical_item': self.critical_item,
            'phantom_bom': self.phantom_bom,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by,
            'updated_by': self.updated_by,
        }
    
    def __str__(self):
        return f"{self.item_no} - {self.description}"
