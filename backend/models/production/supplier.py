# backend/models/production/supplier.py
"""
Supplier Model (NAV/BC-style)
Vendors/Suppliers for purchasing management
"""
from mongoengine import (
    Document, StringField, IntField, ListField, DictField, 
    BooleanField, DateTimeField, ReferenceField
)
from datetime import datetime
from models.laboratory import Laboratory


class Supplier(Document):
    """
    Supplier (Vendor) - NAV/BC style
    
    Represents suppliers/vendors for purchasing raw materials and components.
    Links to Items as preferred suppliers.
    """
    meta = {
        'collection': 'suppliers',
        'indexes': [
            {'fields': ['tenant_id', 'supplier_id'], 'unique': True},  # PK logic
            'tenant_id',
            'supplier_id',
            'status',
        ]
    }
    
    # Multi-tenancy
    tenant_id = ReferenceField(Laboratory, required=True, db_field='tenant_id')
    
    # Core identification
    supplier_id = StringField(required=True, max_length=20)  # e.g., "SUP-001"
    name = StringField(required=True, max_length=100)
    name_2 = StringField(max_length=100)  # Secondary name line
    
    # Contact information
    address = StringField(max_length=100)
    address_2 = StringField(max_length=100)
    city = StringField(max_length=50)
    postal_code = StringField(max_length=20)
    country_code = StringField(max_length=2)  # ISO 3166-1 alpha-2
    
    # Communication
    phone_no = StringField(max_length=30)
    mobile_no = StringField(max_length=30)
    email = StringField(max_length=100)
    home_page = StringField(max_length=200)  # Website URL
    
    # Contact persons
    contacts = ListField(DictField())  # [{ name, role, phone, email }]
    
    # Purchasing defaults
    lead_time_days_default = IntField(min_value=0, default=0)  # Default lead time
    currency_code = StringField(max_length=3, default='EUR')  # ISO 4217
    payment_terms_code = StringField(max_length=10)  # Reference to payment terms
    payment_method_code = StringField(max_length=10)  # Reference to payment method
    
    # Preferred items (items this supplier is preferred for)
    preferred_items = ListField(StringField(max_length=20))  # List of item_no
    
    # Rating and classification
    rating = StringField(max_length=20)  # e.g., "A", "B", "C" or custom
    supplier_class = StringField(max_length=20)  # Classification category
    
    # Tax information
    vat_registration_no = StringField(max_length=50)
    tax_id = StringField(max_length=50)
    
    # Financial
    credit_limit = IntField(min_value=0)  # Credit limit amount
    balance = IntField(default=0)  # Current balance (for future use)
    
    # Status
    status = StringField(
        required=True,
        choices=['Active', 'Blocked', 'Suspended'],
        default='Active'
    )
    blocked_reason = StringField(max_length=200)  # Reason if blocked
    
    # Flags
    preferred_supplier = BooleanField(default=False)  # Mark as preferred globally
    
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
            'supplier_id': self.supplier_id,
            'name': self.name,
            'name_2': self.name_2,
            'address': self.address,
            'address_2': self.address_2,
            'city': self.city,
            'postal_code': self.postal_code,
            'country_code': self.country_code,
            'phone_no': self.phone_no,
            'mobile_no': self.mobile_no,
            'email': self.email,
            'home_page': self.home_page,
            'contacts': self.contacts,
            'lead_time_days_default': self.lead_time_days_default,
            'currency_code': self.currency_code,
            'payment_terms_code': self.payment_terms_code,
            'payment_method_code': self.payment_method_code,
            'preferred_items': self.preferred_items,
            'rating': self.rating,
            'supplier_class': self.supplier_class,
            'vat_registration_no': self.vat_registration_no,
            'tax_id': self.tax_id,
            'credit_limit': self.credit_limit,
            'balance': self.balance,
            'status': self.status,
            'blocked_reason': self.blocked_reason,
            'preferred_supplier': self.preferred_supplier,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by,
            'updated_by': self.updated_by,
        }
    
    def __str__(self):
        return f"{self.supplier_id} - {self.name}"
