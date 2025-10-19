"""
Routing Model - NAV/BC-style

A Routing defines the sequence of operations (steps) needed to manufacture an item.
Each operation specifies a work center, setup time, run time, and other details.

NAV/BC Patterns:
- Multi-version support: Same item can have multiple routing versions
- Status lifecycle: New -> Under Development -> Certified -> Closed
- Operation sequence: operation_no (10, 20, 30...) allows insertions
- Time calculation: setup_time (once per batch) + run_time (per unit)
- Concurrent capacities: How many units can be processed simultaneously
"""

from mongoengine import Document, StringField, IntField, FloatField, DateTimeField, EmbeddedDocument, \
    EmbeddedDocumentListField, BooleanField
from datetime import datetime


class RoutingOperation(EmbeddedDocument):
    """
    A single operation in a routing (one step in production process).
    
    NAV/BC Fields:
    - operation_no: Sequence number (10, 20, 30... for easy insertion)
    - work_center_code: Where operation is performed (FK to WorkCenter)
    - description: What happens in this operation
    - setup_time: Time to prepare (minutes, once per production order)
    - run_time: Time per unit (minutes per base quantity)
    - concurrent_capacities: How many units can be processed at once (default 1)
    - scrap_pct: Expected scrap/waste at this operation
    """
    operation_no = IntField(required=True, min_value=1)
    work_center_code = StringField(required=True, max_length=50)
    machine_center_code = StringField(max_length=50)  # Optional, specific machine
    description = StringField(max_length=200)
    
    # Time calculation (in minutes)
    setup_time = FloatField(default=0.0, min_value=0)
    run_time = FloatField(default=0.0, min_value=0)  # Per base quantity
    wait_time = FloatField(default=0.0, min_value=0)  # Queue time before operation
    move_time = FloatField(default=0.0, min_value=0)  # Transport time after operation
    
    # Capacity
    concurrent_capacities = IntField(default=1, min_value=1)
    
    # Scrap
    scrap_pct = FloatField(default=0.0, min_value=0, max_value=100)
    
    # Routing link (connects to BOM line's routing_link_code)
    routing_link_code = StringField(max_length=20)
    
    # Send ahead quantity: Start next operation before all units are complete
    send_ahead_quantity = FloatField(default=0.0, min_value=0)
    
    # Subcontracting
    is_subcontracted = BooleanField(default=False)
    subcontractor_id = StringField(max_length=50)  # FK to Supplier
    
    meta = {
        'strict': False
    }


class Routing(Document):
    """
    Routing - defines operations needed to manufacture an item.
    
    NAV/BC Structure:
    - Header: item_no, version_code, status
    - Operations: List of RoutingOperation (steps)
    
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
    
    # Routing Header
    item_no = StringField(required=True, max_length=50)
    version_code = StringField(required=True, default="V1", max_length=20)
    description = StringField(max_length=200)
    
    # Status
    status = StringField(
        required=True,
        choices=["New", "Under Development", "Certified", "Closed"],
        default="New"
    )
    
    # Operations (steps)
    operations = EmbeddedDocumentListField(RoutingOperation)
    
    # Audit fields
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    created_by = StringField(max_length=100)
    updated_by = StringField(max_length=100)
    
    # Certification tracking
    certified_date = DateTimeField()
    certified_by = StringField(max_length=100)
    
    meta = {
        'collection': 'production_routings',
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
        Certify this Routing version (make it active).
        
        Business Rule (NAV/BC):
        - Only one version per item can be Certified
        - Uncertify any existing Certified version first
        """
        if self.status == "Certified":
            return  # Already certified
        
        # Uncertify other versions of same item
        Routing.objects(
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
        """Close this Routing version (archive)"""
        if self.status == "Closed":
            return
        
        self.status = "Closed"
        self.updated_by = user_email
        self.save()
    
    def calculate_total_time(self, quantity: float) -> dict:
        """
        Calculate total production time for given quantity.
        
        Returns:
            {
                "setup_time_total": float,  # minutes
                "run_time_total": float,    # minutes
                "total_time": float,        # minutes
                "operations": [
                    {
                        "operation_no": int,
                        "description": str,
                        "setup_time": float,
                        "run_time": float,
                        "total_time": float
                    },
                    ...
                ]
            }
        """
        setup_total = 0.0
        run_total = 0.0
        operation_details = []
        
        for op in self.operations:
            # Setup time is fixed per batch
            op_setup = op.setup_time or 0.0
            
            # Run time scales with quantity, adjusted for concurrent capacities
            op_run = ((op.run_time or 0.0) * quantity) / op.concurrent_capacities
            
            op_total = op_setup + op_run
            
            setup_total += op_setup
            run_total += op_run
            
            operation_details.append({
                "operation_no": op.operation_no,
                "work_center_code": op.work_center_code,
                "description": op.description,
                "setup_time": op_setup,
                "run_time": op_run,
                "total_time": op_total
            })
        
        return {
            "setup_time_total": setup_total,
            "run_time_total": run_total,
            "total_time": setup_total + run_total,
            "operations": operation_details
        }
    
    def to_dict(self):
        """Serialize to JSON-compatible dict"""
        return {
            "id": str(self.id),
            "tenant_id": self.tenant_id,
            "item_no": self.item_no,
            "version_code": self.version_code,
            "description": self.description,
            "status": self.status,
            "operations": [
                {
                    "operation_no": op.operation_no,
                    "work_center_code": op.work_center_code,
                    "machine_center_code": op.machine_center_code,
                    "description": op.description,
                    "setup_time": op.setup_time,
                    "run_time": op.run_time,
                    "wait_time": op.wait_time,
                    "move_time": op.move_time,
                    "concurrent_capacities": op.concurrent_capacities,
                    "scrap_pct": op.scrap_pct,
                    "routing_link_code": op.routing_link_code,
                    "send_ahead_quantity": op.send_ahead_quantity,
                    "is_subcontracted": op.is_subcontracted,
                    "subcontractor_id": op.subcontractor_id
                }
                for op in self.operations
            ],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "certified_date": self.certified_date.isoformat() if self.certified_date else None,
            "certified_by": self.certified_by
        }
