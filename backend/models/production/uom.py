# backend/models/production/uom.py
"""
Unit of Measure (UOM) Model
NAV/BC-like Units of Measure for production and inventory management
"""
from mongoengine import Document, StringField, IntField, DateTimeField, ReferenceField
from datetime import datetime
from models.laboratory import Laboratory


class UnitOfMeasure(Document):
    """
    Unit of Measure (UOM) - NAV/BC style
    
    Defines measurement units for items (e.g., PCS, KG, L, H, BOX)
    with decimal precision control.
    """
    meta = {
        'collection': 'units_of_measure',
        'indexes': [
            {'fields': ['tenant_id', 'code'], 'unique': True},  # PK logic
            'tenant_id',
            'code',
        ]
    }
    
    # Multi-tenancy
    tenant_id = ReferenceField(Laboratory, required=True, db_field='tenant_id')
    
    # Core fields
    code = StringField(required=True, max_length=10)  # e.g., "PCS", "KG", "L"
    description = StringField(required=True, max_length=100)  # e.g., "Pieces"
    decimals = IntField(required=True, min_value=0, max_value=6, default=0)  # Decimal places
    
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
            'code': self.code,
            'description': self.description,
            'decimals': self.decimals,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by,
            'updated_by': self.updated_by,
        }
    
    def __str__(self):
        return f"{self.code} - {self.description}"
