# backend/models/production/location.py
"""
Location Model (NAV/BC-style)
Warehouses/Locations for inventory management
"""
from mongoengine import (
    Document, StringField, BooleanField, DateTimeField, ReferenceField
)
from datetime import datetime
from models.laboratory import Laboratory


class Location(Document):
    """
    Location (Warehouse/Storage) - NAV/BC style
    
    Represents physical locations where inventory is stored.
    Controls stock management policies per location.
    """
    meta = {
        'collection': 'locations',
        'indexes': [
            {'fields': ['tenant_id', 'code'], 'unique': True},  # PK logic
            'tenant_id',
            'code',
            'is_default',
        ]
    }
    
    # Multi-tenancy
    tenant_id = ReferenceField(Laboratory, required=True, db_field='tenant_id')
    
    # Core identification
    code = StringField(required=True, max_length=10)  # e.g., "MAIN", "WH01"
    name = StringField(required=True, max_length=100)  # e.g., "Main Warehouse"
    
    # Address info (optional)
    address = StringField(max_length=100)
    address_2 = StringField(max_length=100)
    city = StringField(max_length=50)
    postal_code = StringField(max_length=20)
    country_code = StringField(max_length=2)  # ISO 3166-1 alpha-2
    
    # Contact
    contact_name = StringField(max_length=100)
    phone_no = StringField(max_length=30)
    email = StringField(max_length=100)
    
    # Inventory policies
    allow_negative_stock = BooleanField(default=False)  # Allow negative inventory?
    require_pick = BooleanField(default=False)  # Require pick document for shipment?
    require_put_away = BooleanField(default=False)  # Require put-away for receipt?
    
    # Default location
    is_default = BooleanField(default=False)  # Default location for transactions
    
    # Status
    blocked = BooleanField(default=False)  # Block transactions if true
    
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
            'name': self.name,
            'address': self.address,
            'address_2': self.address_2,
            'city': self.city,
            'postal_code': self.postal_code,
            'country_code': self.country_code,
            'contact_name': self.contact_name,
            'phone_no': self.phone_no,
            'email': self.email,
            'allow_negative_stock': self.allow_negative_stock,
            'require_pick': self.require_pick,
            'require_put_away': self.require_put_away,
            'is_default': self.is_default,
            'blocked': self.blocked,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by,
            'updated_by': self.updated_by,
        }
    
    def __str__(self):
        return f"{self.code} - {self.name}"
