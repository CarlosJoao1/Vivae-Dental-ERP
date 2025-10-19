"""
Bill of Materials (BOM) Model - NAV/BC-style

A BOM defines the components needed to manufacture an item.
Each BOM has a header (item_no, version) and lines (components).

NAV/BC Patterns:
- Multi-version support: Same item can have multiple BOM versions (draft, certified, historical)
- Status lifecycle: New -> Under Development -> Certified -> Closed
- Line positioning: position field for sorting/grouping operations
- Scrap percentage: Accounts for waste in material calculations
- Phantom BOMs: Components that explode directly into parent (no inventory tracking)
"""

from mongoengine import Document, StringField, IntField, FloatField, DateTimeField, EmbeddedDocument, \
    EmbeddedDocumentListField, BooleanField
from datetime import datetime


class BOMLine(EmbeddedDocument):
    """
    A single line in a BOM (one component).
    
    NAV/BC Fields:
    - line_no: Unique within BOM, used for referencing/updates
    - component_item_no: The item consumed (FK to Item)
    - component_type: Item (normal component) or Resource (labor/machine time)
    - quantity_per: How many units of component per 1 unit of parent (base UOM)
    - scrap_pct: Waste percentage (e.g., 5% means 1.05 units needed for 1 unit output)
    - position: Free-text field for grouping (e.g., "Frame", "Wheels", "Electronics")
    - position_2/position_3: Additional grouping levels (optional)
    """
    line_no = IntField(required=True, min_value=1)
    component_type = StringField(required=True, choices=["Item", "Resource"], default="Item")
    component_item_no = StringField(required=True, max_length=50)
    description = StringField(max_length=200)
    
    quantity_per = FloatField(required=True, min_value=0.000001)
    uom_code = StringField(max_length=20)  # Component's UOM (usually base UOM)
    
    scrap_pct = FloatField(default=0.0, min_value=0, max_value=100)
    
    # Positioning for grouping/sorting
    position = StringField(max_length=50)
    position_2 = StringField(max_length=50)
    position_3 = StringField(max_length=50)
    
    # Routing link (optional): which operation consumes this component
    routing_link_code = StringField(max_length=20)
    
    # Length/Width calculation support (for cutting operations)
    length = FloatField(min_value=0)
    width = FloatField(min_value=0)
    depth = FloatField(min_value=0)
    weight = FloatField(min_value=0)
    
    # Lead Time Offset: When to start this component (days before parent due date)
    lead_time_offset = IntField(default=0, min_value=0)
    
    meta = {
        'strict': False
    }


class BOM(Document):
    """
    Bill of Materials - defines components needed to manufacture an item.
    
    NAV/BC Structure:
    - Header: item_no, version_code, status
    - Lines: List of BOMLine (components)
    
    Versioning:
    - Same item_no can have multiple versions (e.g., "V1", "V2", "DRAFT")
    - Only one version can be "Certified" (active) at a time per item
    - Old versions can be "Closed" for history
    
    Status Lifecycle:
    - New: Just created, not validated
    - Under Development: Being edited/tested
    - Certified: Active version, used in production
    - Closed: Historical version, read-only
    """
    # Multi-tenancy
    tenant_id = StringField(required=True, max_length=100)
    
    # BOM Header
    item_no = StringField(required=True, max_length=50)
    version_code = StringField(required=True, default="V1", max_length=20)
    description = StringField(max_length=200)
    
    # Status
    status = StringField(
        required=True,
        choices=["New", "Under Development", "Certified", "Closed"],
        default="New"
    )
    
    # Base quantity (usually 1.0, but can be batch size like 100 for efficiency)
    base_quantity = FloatField(default=1.0, min_value=0.000001)
    base_uom = StringField(max_length=20)
    
    # Lines (components)
    lines = EmbeddedDocumentListField(BOMLine)
    
    # Phantom BOM: If true, components explode directly into parent BOM
    # (no intermediate inventory tracking)
    is_phantom = BooleanField(default=False)
    
    # Lead time calculation
    # If set, overrides item's default lead_time_days
    production_lead_time_days = IntField(min_value=0)
    
    # Audit fields
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    created_by = StringField(max_length=100)
    updated_by = StringField(max_length=100)
    
    # Certification tracking
    certified_date = DateTimeField()
    certified_by = StringField(max_length=100)
    
    meta = {
        'collection': 'production_boms',
        'indexes': [
            {
                'fields': ['tenant_id', 'item_no', 'version_code'],
                'unique': True
            },
            'tenant_id',
            'item_no',
            'status',
            ('tenant_id', 'status'),
            ('tenant_id', 'item_no', 'status')
        ],
        'strict': False,
        'ordering': ['item_no', 'version_code']
    }
    
    def save(self, *args, **kwargs):
        """Override save to update timestamp"""
        self.updated_at = datetime.utcnow()
        return super().save(*args, **kwargs)
    
    def certify(self, user_email: str):
        """
        Certify this BOM version (make it active).
        
        Business Rule (NAV/BC):
        - Only one version per item can be Certified
        - Uncertify any existing Certified version first
        """
        if self.status == "Certified":
            return  # Already certified
        
        # Uncertify other versions of same item
        BOM.objects(
            tenant_id=self.tenant_id,
            item_no=self.item_no,
            status="Certified"
        ).update(
            set__status="Closed",
            set__updated_at=datetime.utcnow()
        )
        
        # Certify this version
        self.status = "Certified"
        self.certified_date = datetime.utcnow()
        self.certified_by = user_email
        self.updated_by = user_email
        self.save()
    
    def close(self, user_email: str):
        """Close this BOM version (archive)"""
        if self.status == "Closed":
            return
        
        self.status = "Closed"
        self.updated_by = user_email
        self.save()
    
    def to_dict(self):
        """Serialize to JSON-compatible dict"""
        return {
            "id": str(self.id),
            "tenant_id": self.tenant_id,
            "item_no": self.item_no,
            "version_code": self.version_code,
            "description": self.description,
            "status": self.status,
            "base_quantity": self.base_quantity,
            "base_uom": self.base_uom,
            "is_phantom": self.is_phantom,
            "production_lead_time_days": self.production_lead_time_days,
            "lines": [
                {
                    "line_no": line.line_no,
                    "component_type": line.component_type,
                    "component_item_no": line.component_item_no,
                    "description": line.description,
                    "quantity_per": line.quantity_per,
                    "uom_code": line.uom_code,
                    "scrap_pct": line.scrap_pct,
                    "position": line.position,
                    "position_2": line.position_2,
                    "position_3": line.position_3,
                    "routing_link_code": line.routing_link_code,
                    "lead_time_offset": line.lead_time_offset
                }
                for line in self.lines
            ],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "certified_date": self.certified_date.isoformat() if self.certified_date else None,
            "certified_by": self.certified_by
        }
