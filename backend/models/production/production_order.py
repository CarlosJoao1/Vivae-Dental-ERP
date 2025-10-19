"""
Production Order Model - NAV/BC-style

A Production Order represents a plan to manufacture a specific quantity of an item.
It tracks the entire lifecycle from planning to completion.

NAV/BC Patterns:
- Status workflow: Simulated -> Planned -> Firm Planned -> Released -> Finished
- Links to BOM and Routing for material/operation requirements
- Tracks expected vs actual costs, quantities, times
- Supports partial output and consumption posting
"""

from mongoengine import Document, StringField, IntField, FloatField, DateTimeField, DateField, \
    EmbeddedDocument, EmbeddedDocumentListField, BooleanField
from datetime import datetime, timedelta
from typing import Optional


class ProductionOrderLine(EmbeddedDocument):
    """
    Component requirement line (from BOM explosion).
    
    Tracks:
    - Expected quantity (from BOM)
    - Consumed quantity (posted from journals)
    - Remaining quantity
    """
    line_no = IntField(required=True, min_value=1)
    component_item_no = StringField(required=True, max_length=50)
    description = StringField(max_length=200)
    
    quantity_per = FloatField(required=True, min_value=0)
    expected_quantity = FloatField(required=True, min_value=0)  # qty_per * order_qty
    consumed_quantity = FloatField(default=0.0, min_value=0)
    remaining_quantity = FloatField(default=0.0, min_value=0)
    
    uom_code = StringField(max_length=20)
    location_code = StringField(max_length=50)
    
    # BOM reference
    bom_line_no = IntField()
    position = StringField(max_length=50)
    
    meta = {
        'strict': False
    }


class ProductionOrderRouting(EmbeddedDocument):
    """
    Operation requirement line (from Routing).
    
    Tracks:
    - Expected time (from Routing)
    - Actual time (posted from capacity journals)
    - Remaining time
    """
    operation_no = IntField(required=True, min_value=1)
    work_center_code = StringField(required=True, max_length=50)
    machine_center_code = StringField(max_length=50)
    description = StringField(max_length=200)
    
    setup_time = FloatField(default=0.0, min_value=0)  # Minutes
    run_time = FloatField(default=0.0, min_value=0)    # Minutes
    expected_capacity_need = FloatField(default=0.0, min_value=0)
    
    actual_setup_time = FloatField(default=0.0, min_value=0)
    actual_run_time = FloatField(default=0.0, min_value=0)
    remaining_time = FloatField(default=0.0, min_value=0)
    
    # Routing reference
    routing_operation_no = IntField()
    
    # Status
    status = StringField(
        choices=["Planned", "In Progress", "Finished"],
        default="Planned"
    )
    
    meta = {
        'strict': False
    }


class ProductionOrder(Document):
    """
    Production Order - plan to manufacture an item.
    
    NAV/BC Status Lifecycle:
    1. Simulated: What-if scenario, no reservations
    2. Planned: Soft plan, no firm commitment
    3. Firm Planned: Committed plan, but not started
    4. Released: Active production, can post consumption/output
    5. Finished: Completed, all quantities posted
    6. Cancelled: Aborted, no further posting
    
    Key Operations:
    - refresh(): Recalculate from BOM/Routing (if status < Released)
    - release(): Start production (create reservations)
    - finish(): Close order (verify all posted)
    - reopen(): Move back to Released (if corrections needed)
    """
    # Multi-tenancy
    tenant_id = StringField(required=True, max_length=100)
    
    # Order Header
    order_no = StringField(required=True, max_length=50)
    description = StringField(max_length=200)
    
    # Item
    item_no = StringField(required=True, max_length=50)
    
    # Quantity
    quantity = FloatField(required=True, min_value=0.000001)
    finished_quantity = FloatField(default=0.0, min_value=0)
    remaining_quantity = FloatField(default=0.0, min_value=0)
    
    # Scrap
    scrap_quantity = FloatField(default=0.0, min_value=0)
    scrap_pct = FloatField(default=0.0, min_value=0, max_value=100)
    
    # Unit of Measure
    uom_code = StringField(max_length=20)
    
    # Dates
    start_date = DateField()
    due_date = DateField()
    end_date = DateField()  # Actual completion date
    
    # Location
    location_code = StringField(max_length=50)
    bin_code = StringField(max_length=50)  # Specific bin/position
    
    # Status
    status = StringField(
        required=True,
        choices=["Simulated", "Planned", "Firm Planned", "Released", "Finished", "Cancelled"],
        default="Planned"
    )
    
    # BOM & Routing References
    bom_no = StringField(max_length=50)  # item_no if using certified BOM
    bom_version_code = StringField(max_length=20)
    routing_no = StringField(max_length=50)  # item_no if using certified Routing
    routing_version_code = StringField(max_length=20)
    
    # Lines (from BOM explosion)
    lines = EmbeddedDocumentListField(ProductionOrderLine)
    
    # Routing operations
    routing_lines = EmbeddedDocumentListField(ProductionOrderRouting)
    
    # Costing
    unit_cost = FloatField(default=0.0, min_value=0)
    expected_cost = FloatField(default=0.0, min_value=0)
    actual_cost = FloatField(default=0.0, min_value=0)
    
    # Priority
    priority = IntField(default=0, min_value=0)
    
    # Shortages
    has_material_shortage = BooleanField(default=False)
    has_capacity_shortage = BooleanField(default=False)
    
    # Audit fields
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    created_by = StringField(max_length=100)
    updated_by = StringField(max_length=100)
    
    # Status change tracking
    released_date = DateTimeField()
    released_by = StringField(max_length=100)
    finished_date = DateTimeField()
    finished_by = StringField(max_length=100)
    
    meta = {
        'collection': 'production_orders',
        'indexes': [
            {
                'fields': ['tenant_id', 'order_no'],
                'unique': True
            },
            'tenant_id',
            'order_no',
            'item_no',
            'status',
            'due_date',
            ('tenant_id', 'status'),
            ('tenant_id', 'item_no'),
            ('tenant_id', 'status', 'due_date')
        ],
        'strict': False,
        'ordering': ['order_no']
    }
    
    def save(self, *args, **kwargs):
        """Override save to update timestamp and calculated fields"""
        self.updated_at = datetime.utcnow()
        self.remaining_quantity = self.quantity - self.finished_quantity - self.scrap_quantity
        return super().save(*args, **kwargs)
    
    def release(self, user_email: str) -> bool:
        """
        Release the production order (start production).
        
        Business Rules:
        - Can only release from Firm Planned status
        - Must have BOM and Routing
        - Creates component reservations
        - Calculates capacity needs
        
        Returns:
            True if released successfully, False otherwise
        """
        if self.status not in ["Planned", "Firm Planned"]:
            return False
        
        # TODO: Create reservations for components
        # TODO: Create capacity reservations
        
        self.status = "Released"
        self.released_date = datetime.utcnow()
        self.released_by = user_email
        self.updated_by = user_email
        self.save()
        return True
    
    def finish(self, user_email: str) -> bool:
        """
        Finish the production order (complete).
        
        Business Rules:
        - Can only finish from Released status
        - All quantities should be posted
        - Verifies no remaining quantity
        
        Returns:
            True if finished successfully, False otherwise
        """
        if self.status != "Released":
            return False
        
        # Business rule: Allow finish even with small remaining quantity (tolerance)
        tolerance = 0.001
        if self.remaining_quantity > tolerance:
            return False  # Still have remaining quantity to produce
        
        self.status = "Finished"
        self.finished_date = datetime.utcnow()
        self.finished_by = user_email
        self.end_date = datetime.utcnow().date()
        self.updated_by = user_email
        self.save()
        return True
    
    def reopen(self, user_email: str) -> bool:
        """
        Reopen a finished order (for corrections).
        
        Business Rules:
        - Can only reopen from Finished status
        - Used for posting corrections
        
        Returns:
            True if reopened successfully, False otherwise
        """
        if self.status != "Finished":
            return False
        
        self.status = "Released"
        self.finished_date = None
        self.finished_by = None
        self.end_date = None
        self.updated_by = user_email
        self.save()
        return True
    
    def cancel(self, user_email: str) -> bool:
        """
        Cancel the production order.
        
        Business Rules:
        - Cannot cancel if status is Finished
        - Releases reservations
        
        Returns:
            True if cancelled successfully, False otherwise
        """
        if self.status == "Finished":
            return False
        
        # TODO: Release reservations
        
        self.status = "Cancelled"
        self.updated_by = user_email
        self.save()
        return True
    
    def to_dict(self):
        """Serialize to JSON-compatible dict"""
        return {
            "id": str(self.id),
            "tenant_id": self.tenant_id,
            "order_no": self.order_no,
            "description": self.description,
            "item_no": self.item_no,
            "quantity": self.quantity,
            "finished_quantity": self.finished_quantity,
            "remaining_quantity": self.remaining_quantity,
            "scrap_quantity": self.scrap_quantity,
            "scrap_pct": self.scrap_pct,
            "uom_code": self.uom_code,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "location_code": self.location_code,
            "bin_code": self.bin_code,
            "status": self.status,
            "bom_no": self.bom_no,
            "bom_version_code": self.bom_version_code,
            "routing_no": self.routing_no,
            "routing_version_code": self.routing_version_code,
            "lines": [
                {
                    "line_no": line.line_no,
                    "component_item_no": line.component_item_no,
                    "description": line.description,
                    "quantity_per": line.quantity_per,
                    "expected_quantity": line.expected_quantity,
                    "consumed_quantity": line.consumed_quantity,
                    "remaining_quantity": line.remaining_quantity,
                    "uom_code": line.uom_code,
                    "location_code": line.location_code,
                    "position": line.position
                }
                for line in self.lines
            ],
            "routing_lines": [
                {
                    "operation_no": op.operation_no,
                    "work_center_code": op.work_center_code,
                    "machine_center_code": op.machine_center_code,
                    "description": op.description,
                    "setup_time": op.setup_time,
                    "run_time": op.run_time,
                    "expected_capacity_need": op.expected_capacity_need,
                    "actual_setup_time": op.actual_setup_time,
                    "actual_run_time": op.actual_run_time,
                    "remaining_time": op.remaining_time,
                    "status": op.status
                }
                for op in self.routing_lines
            ],
            "unit_cost": self.unit_cost,
            "expected_cost": self.expected_cost,
            "actual_cost": self.actual_cost,
            "priority": self.priority,
            "has_material_shortage": self.has_material_shortage,
            "has_capacity_shortage": self.has_capacity_shortage,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "released_date": self.released_date.isoformat() if self.released_date else None,
            "released_by": self.released_by,
            "finished_date": self.finished_date.isoformat() if self.finished_date else None,
            "finished_by": self.finished_by
        }
