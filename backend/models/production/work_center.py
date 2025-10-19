"""
Work Center and Machine Center Models - NAV/BC-style

Work Centers represent production resources (manufacturing cells, departments).
Machine Centers are specific machines within a work center.

NAV/BC Patterns:
- Capacity: Measured in time units (minutes/hours per day)
- Efficiency: Actual vs theoretical capacity (e.g., 85% = 0.85)
- Calendar: Links to capacity calendar for shifts/holidays
- Unit Cost: Cost per minute/hour for capacity costing
"""

from mongoengine import Document, StringField, IntField, FloatField, DateTimeField, BooleanField, DateField
from datetime import datetime


class WorkCenter(Document):
    """
    Work Center - a production resource (manufacturing cell, department).
    
    NAV/BC Fields:
    - code: Unique identifier (e.g., "ASSEMBLY", "WELDING", "PAINT")
    - name: Display name
    - capacity: Available time per day (minutes)
    - efficiency_pct: Actual vs theoretical capacity (e.g., 85.0 = 85%)
    - calendar_code: FK to Calendar for shifts/holidays
    - unit_cost: Cost per minute of capacity usage
    """
    # Multi-tenancy
    tenant_id = StringField(required=True, max_length=100)
    
    # Work Center Header
    code = StringField(required=True, max_length=50)
    name = StringField(required=True, max_length=200)
    description = StringField(max_length=500)
    
    # Work Center Type
    work_center_type = StringField(
        choices=["Machine Center", "Work Center", "Person"],
        default="Work Center"
    )
    
    # Capacity
    capacity = FloatField(default=480.0, min_value=0)  # Minutes per day (8 hours default)
    efficiency_pct = FloatField(default=100.0, min_value=0, max_value=200)
    
    # Calendar
    calendar_code = StringField(max_length=50)  # FK to Calendar (future)
    
    # Costing
    unit_cost = FloatField(default=0.0, min_value=0)  # Cost per minute
    overhead_rate = FloatField(default=0.0, min_value=0)  # Overhead percentage
    
    # Location
    location_code = StringField(max_length=50)  # FK to Location
    
    # Status
    blocked = BooleanField(default=False)
    
    # Queuing
    queue_time = FloatField(default=0.0, min_value=0)  # Default wait time (minutes)
    
    # Audit fields
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    created_by = StringField(max_length=100)
    updated_by = StringField(max_length=100)
    
    meta = {
        'collection': 'production_work_centers',
        'indexes': [
            {
                'fields': ['tenant_id', 'code'],
                'unique': True
            },
            'tenant_id',
            'code',
            ('tenant_id', 'blocked')
        ],
        'strict': False,
        'ordering': ['code']
    }
    
    def save(self, *args, **kwargs):
        """Override save to update timestamp"""
        self.updated_at = datetime.utcnow()
        return super().save(*args, **kwargs)
    
    def calculate_effective_capacity(self) -> float:
        """
        Calculate effective capacity considering efficiency.
        
        Returns:
            Effective capacity in minutes per day
        """
        return self.capacity * (self.efficiency_pct / 100.0)
    
    def to_dict(self):
        """Serialize to JSON-compatible dict"""
        return {
            "id": str(self.id),
            "tenant_id": self.tenant_id,
            "code": self.code,
            "name": self.name,
            "description": self.description,
            "work_center_type": self.work_center_type,
            "capacity": self.capacity,
            "efficiency_pct": self.efficiency_pct,
            "effective_capacity": self.calculate_effective_capacity(),
            "calendar_code": self.calendar_code,
            "unit_cost": self.unit_cost,
            "overhead_rate": self.overhead_rate,
            "location_code": self.location_code,
            "blocked": self.blocked,
            "queue_time": self.queue_time,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
            "updated_by": self.updated_by
        }


class MachineCenter(Document):
    """
    Machine Center - a specific machine within a work center.
    
    NAV/BC Fields:
    - Inherits all Work Center fields
    - Adds maintenance tracking
    - Links to parent Work Center
    """
    # Multi-tenancy
    tenant_id = StringField(required=True, max_length=100)
    
    # Machine Center Header
    code = StringField(required=True, max_length=50)
    name = StringField(required=True, max_length=200)
    description = StringField(max_length=500)
    
    # Parent Work Center
    work_center_code = StringField(required=True, max_length=50)  # FK to WorkCenter
    
    # Capacity (inherits from Work Center, but can override)
    capacity = FloatField(default=480.0, min_value=0)
    efficiency_pct = FloatField(default=100.0, min_value=0, max_value=200)
    
    # Calendar
    calendar_code = StringField(max_length=50)
    
    # Costing
    unit_cost = FloatField(default=0.0, min_value=0)
    overhead_rate = FloatField(default=0.0, min_value=0)
    
    # Location
    location_code = StringField(max_length=50)
    
    # Status
    blocked = BooleanField(default=False)
    
    # Queuing
    queue_time = FloatField(default=0.0, min_value=0)
    
    # Maintenance (Machine-specific)
    maintenance_interval_days = IntField(min_value=0)  # Days between maintenance
    next_maintenance_date = DateField()
    last_maintenance_date = DateField()
    
    # Machine Details
    manufacturer = StringField(max_length=200)
    model = StringField(max_length=200)
    serial_number = StringField(max_length=100)
    purchase_date = DateField()
    
    # Audit fields
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    created_by = StringField(max_length=100)
    updated_by = StringField(max_length=100)
    
    meta = {
        'collection': 'production_machine_centers',
        'indexes': [
            {
                'fields': ['tenant_id', 'code'],
                'unique': True
            },
            'tenant_id',
            'code',
            'work_center_code',
            ('tenant_id', 'blocked'),
            ('tenant_id', 'work_center_code')
        ],
        'strict': False,
        'ordering': ['code']
    }
    
    def save(self, *args, **kwargs):
        """Override save to update timestamp"""
        self.updated_at = datetime.utcnow()
        return super().save(*args, **kwargs)
    
    def calculate_effective_capacity(self) -> float:
        """
        Calculate effective capacity considering efficiency.
        
        Returns:
            Effective capacity in minutes per day
        """
        return self.capacity * (self.efficiency_pct / 100.0)
    
    def is_maintenance_due(self) -> bool:
        """Check if maintenance is due"""
        if not self.next_maintenance_date:
            return False
        return datetime.utcnow().date() >= self.next_maintenance_date
    
    def to_dict(self):
        """Serialize to JSON-compatible dict"""
        return {
            "id": str(self.id),
            "tenant_id": self.tenant_id,
            "code": self.code,
            "name": self.name,
            "description": self.description,
            "work_center_code": self.work_center_code,
            "capacity": self.capacity,
            "efficiency_pct": self.efficiency_pct,
            "effective_capacity": self.calculate_effective_capacity(),
            "calendar_code": self.calendar_code,
            "unit_cost": self.unit_cost,
            "overhead_rate": self.overhead_rate,
            "location_code": self.location_code,
            "blocked": self.blocked,
            "queue_time": self.queue_time,
            "maintenance_interval_days": self.maintenance_interval_days,
            "next_maintenance_date": self.next_maintenance_date.isoformat() if self.next_maintenance_date else None,
            "last_maintenance_date": self.last_maintenance_date.isoformat() if self.last_maintenance_date else None,
            "is_maintenance_due": self.is_maintenance_due(),
            "manufacturer": self.manufacturer,
            "model": self.model,
            "serial_number": self.serial_number,
            "purchase_date": self.purchase_date.isoformat() if self.purchase_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
            "updated_by": self.updated_by
        }
