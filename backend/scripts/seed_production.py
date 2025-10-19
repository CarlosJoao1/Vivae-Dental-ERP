# backend/scripts/seed_production.py
"""
Seed Production Master Data & Core Production Entities (NAV/BC-style)
Creates comprehensive seed data for production module testing

Master Data Seeds:
- 5 UOMs: PCS, KG, L, H, BOX
- 1 Location: MAIN (default)
- 1 Supplier: SUP-ABC (lead time 2 days)
- 3 Items: FG-CHAIR (manufactured), RM-WOOD, RM-SCREW (purchased)

Core Production Seeds:
- 3 Work Centers: ASSEMBLY, MACHINING, PAINT
- 2 Machine Centers: CNC-001, LATHE-001
- 1 BOM: FG-CHAIR-001 V1 (Certified)
- 1 Routing: FG-CHAIR-001 V1 (Certified)
- 2 Production Orders: Planned + Released status
"""
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mongoengine import connect
from models.laboratory import Laboratory
from models.production import (
    UnitOfMeasure, Item, Location, Supplier,
    WorkCenter, MachineCenter, BOM, BOMLine, Routing, RoutingOperation, ProductionOrder
)


def seed_production_data():
    """Seed production master data"""
    
    # Connect to database
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/vivae_dental_erp")
    connect(host=mongo_uri)
    
    print("🌱 Seeding Production Master Data...")
    
    # Get default lab (or create one)
    lab = Laboratory.objects.first()
    if not lab:
        lab = Laboratory(name="Demo Dental Lab", active=True).save()
        print(f"✅ Created default laboratory: {lab.name}")
    
    print(f"📍 Using laboratory: {lab.name} ({lab.id})")
    
    # ========================================
    # 1. UNITS OF MEASURE (UOM)
    # ========================================
    print("\n📏 Seeding Units of Measure...")
    
    uoms_data = [
        {"code": "PCS", "description": "Pieces", "decimals": 0},
        {"code": "KG", "description": "Kilograms", "decimals": 3},
        {"code": "L", "description": "Liters", "decimals": 3},
        {"code": "H", "description": "Hours", "decimals": 2},
        {"code": "BOX", "description": "Boxes", "decimals": 0},
    ]
    
    for uom_data in uoms_data:
        # Check if exists
        existing = UnitOfMeasure.objects(tenant_id=lab, code=uom_data["code"]).first()
        if existing:
            print(f"  ⏩ UOM '{uom_data['code']}' already exists")
            continue
        
        uom = UnitOfMeasure(
            tenant_id=lab,
            code=uom_data["code"],
            description=uom_data["description"],
            decimals=uom_data["decimals"],
            created_by="seed_script",
            updated_by="seed_script",
        ).save()
        print(f"  ✅ Created UOM: {uom.code} - {uom.description}")
    
    # ========================================
    # 2. LOCATIONS
    # ========================================
    print("\n📦 Seeding Locations...")
    
    # MAIN location
    existing_loc = Location.objects(tenant_id=lab, code="MAIN").first()
    if existing_loc:
        print(f"  ⏩ Location 'MAIN' already exists")
    else:
        location = Location(
            tenant_id=lab,
            code="MAIN",
            name="Main Warehouse",
            address="123 Industrial Street",
            city="Porto",
            postal_code="4000-123",
            country_code="PT",
            allow_negative_stock=False,
            is_default=True,
            blocked=False,
            created_by="seed_script",
            updated_by="seed_script",
        ).save()
        print(f"  ✅ Created Location: {location.code} - {location.name} (default)")
    
    # ========================================
    # 3. SUPPLIERS
    # ========================================
    print("\n🏭 Seeding Suppliers...")
    
    existing_sup = Supplier.objects(tenant_id=lab, supplier_id="SUP-ABC").first()
    if existing_sup:
        print(f"  ⏩ Supplier 'SUP-ABC' already exists")
    else:
        supplier = Supplier(
            tenant_id=lab,
            supplier_id="SUP-ABC",
            name="ABC Materials & Supplies Ltd.",
            address="456 Supplier Avenue",
            city="Lisbon",
            postal_code="1000-456",
            country_code="PT",
            phone_no="+351 21 234 5678",
            email="orders@abc-supplies.pt",
            lead_time_days_default=2,
            currency_code="EUR",
            preferred_items=["RM-WOOD", "RM-SCREW"],  # Will create these items next
            rating="A",
            status="Active",
            preferred_supplier=True,
            created_by="seed_script",
            updated_by="seed_script",
        ).save()
        print(f"  ✅ Created Supplier: {supplier.supplier_id} - {supplier.name}")
        print(f"     Lead time: {supplier.lead_time_days_default} days")
    
    # ========================================
    # 4. ITEMS
    # ========================================
    print("\n📦 Seeding Items...")
    
    items_data = [
        {
            "item_no": "FG-CHAIR-001",
            "description": "Dental Chair Complete Assembly",
            "item_type": "manufactured",
            "base_uom": "PCS",
            "lead_time_days": 5,  # Production lead time
            "safety_stock_qty": 2,
            "reorder_point": 5,
            "reorder_quantity": 10,
            "unit_cost": 1500.00,
            "status": "Active",
            "critical_item": True,
        },
        {
            "item_no": "RM-WOOD-PLY",
            "description": "Plywood Board 1.2m x 2.4m",
            "item_type": "purchased",
            "base_uom": "PCS",
            "default_supplier_id": "SUP-ABC",
            "lead_time_days": 2,  # Purchase lead time
            "safety_stock_qty": 20,
            "reorder_point": 30,
            "reorder_quantity": 50,
            "unit_cost": 25.50,
            "status": "Active",
        },
        {
            "item_no": "RM-SCREW-M6",
            "description": "Screw M6x20mm Stainless Steel",
            "item_type": "purchased",
            "base_uom": "PCS",
            "default_supplier_id": "SUP-ABC",
            "lead_time_days": 2,
            "safety_stock_qty": 1000,
            "reorder_point": 1500,
            "reorder_quantity": 5000,
            "unit_cost": 0.15,
            "status": "Active",
        },
    ]
    
    for item_data in items_data:
        # Check if exists
        existing_item = Item.objects(tenant_id=lab, item_no=item_data["item_no"]).first()
        if existing_item:
            print(f"  ⏩ Item '{item_data['item_no']}' already exists")
            continue
        
        item = Item(
            tenant_id=lab,
            item_no=item_data["item_no"],
            description=item_data["description"],
            item_type=item_data["item_type"],
            base_uom=item_data["base_uom"],
            default_supplier_id=item_data.get("default_supplier_id"),
            lead_time_days=item_data["lead_time_days"],
            safety_stock_qty=item_data["safety_stock_qty"],
            reorder_point=item_data.get("reorder_point"),
            reorder_quantity=item_data.get("reorder_quantity"),
            unit_cost=item_data["unit_cost"],
            costing_method="standard",
            status=item_data["status"],
            critical_item=item_data.get("critical_item", False),
            created_by="seed_script",
            updated_by="seed_script",
        ).save()
        
        item_type_emoji = "🏭" if item.item_type == "manufactured" else "📦"
        print(f"  ✅ Created Item: {item_type_emoji} {item.item_no} - {item.description}")
        print(f"     Type: {item.item_type}, UOM: {item.base_uom}, Lead time: {item.lead_time_days} days")
    
    # ========================================
    # 5. WORK CENTERS
    # ========================================
    print("\n🏭 Seeding Work Centers...")
    
    work_centers_data = [
        {
            "code": "ASSEMBLY",
            "name": "Assembly Department",
            "description": "Main assembly line for production",
            "location_code": "MAIN",
            "capacity": 480.0,  # 8 hours * 60 minutes
            "efficiency_pct": 85.0,
            "unit_cost": 0.25,  # €15/hour = €0.25/minute
            "overhead_rate": 25.0,
            "blocked": False,
        },
        {
            "code": "MACHINING",
            "name": "Machining Department",
            "description": "CNC machining and precision cutting",
            "location_code": "MAIN",
            "capacity": 480.0,
            "efficiency_pct": 90.0,
            "unit_cost": 0.33,  # €20/hour = €0.33/minute
            "overhead_rate": 30.0,
            "blocked": False,
        },
        {
            "code": "PAINT",
            "name": "Paint & Finishing Department",
            "description": "Painting, coating, and final finishing",
            "location_code": "MAIN",
            "capacity": 240.0,  # 4 hours * 60 minutes
            "efficiency_pct": 75.0,
            "unit_cost": 0.20,  # €12/hour = €0.20/minute
            "overhead_rate": 20.0,
            "blocked": False,
        },
    ]
    
    for wc_data in work_centers_data:
        existing_wc = WorkCenter.objects(tenant_id=str(lab.id), code=wc_data["code"]).first()
        if existing_wc:
            print(f"  ⏩ Work Center '{wc_data['code']}' already exists")
            continue
        
        wc = WorkCenter(
            tenant_id=str(lab.id),
            code=wc_data["code"],
            name=wc_data["name"],
            description=wc_data.get("description"),
            location_code=wc_data["location_code"],
            capacity=wc_data["capacity"],
            efficiency_pct=wc_data["efficiency_pct"],
            unit_cost=wc_data["unit_cost"],
            overhead_rate=wc_data["overhead_rate"],
            blocked=wc_data.get("blocked", False),
            created_by="seed_script",
            updated_by="seed_script",
        ).save()
        print(f"  ✅ Created Work Center: {wc.code} - {wc.name}")
        print(f"     Capacity: {wc.capacity}min/day, Efficiency: {wc.efficiency_pct}%, Cost: €{wc.unit_cost}/min")
    
    # ========================================
    # 6. MACHINE CENTERS
    # ========================================
    print("\n⚙️ Seeding Machine Centers...")
    
    machine_centers_data = [
        {
            "code": "CNC-001",
            "name": "CNC Milling Machine #1",
            "description": "5-axis CNC milling center",
            "work_center_code": "MACHINING",
            "location_code": "MAIN",
            "capacity": 480.0,
            "efficiency_pct": 92.0,
            "unit_cost": 0.42,  # €25/hour = €0.42/minute
            "overhead_rate": 35.0,
            "blocked": False,
        },
        {
            "code": "LATHE-001",
            "name": "CNC Lathe #1",
            "description": "High-precision CNC lathe",
            "work_center_code": "MACHINING",
            "location_code": "MAIN",
            "capacity": 480.0,
            "efficiency_pct": 88.0,
            "unit_cost": 0.37,  # €22/hour = €0.37/minute
            "overhead_rate": 32.0,
            "blocked": False,
        },
    ]
    
    for mc_data in machine_centers_data:
        existing_mc = MachineCenter.objects(tenant_id=str(lab.id), code=mc_data["code"]).first()
        if existing_mc:
            print(f"  ⏩ Machine Center '{mc_data['code']}' already exists")
            continue
        
        mc = MachineCenter(
            tenant_id=str(lab.id),
            code=mc_data["code"],
            name=mc_data["name"],
            description=mc_data.get("description"),
            work_center_code=mc_data["work_center_code"],
            location_code=mc_data["location_code"],
            capacity=mc_data["capacity"],
            efficiency_pct=mc_data["efficiency_pct"],
            unit_cost=mc_data["unit_cost"],
            overhead_rate=mc_data["overhead_rate"],
            blocked=mc_data.get("blocked", False),
            created_by="seed_script",
            updated_by="seed_script",
        ).save()
        print(f"  ✅ Created Machine Center: {mc.code} - {mc.name}")
        print(f"     Work Center: {mc.work_center_code}, Efficiency: {mc.efficiency_pct}%")
    
    # ========================================
    # 7. BOMs (BILL OF MATERIALS)
    # ========================================
    print("\n📋 Seeding BOMs...")
    
    # BOM for FG-CHAIR-001
    existing_bom = BOM.objects(tenant_id=str(lab.id), item_no="FG-CHAIR-001", version_code="V1").first()
    if existing_bom:
        print(f"  ⏩ BOM for 'FG-CHAIR-001 V1' already exists")
    else:
        bom_lines = [
            BOMLine(
                line_no=10,
                component_item_no="RM-WOOD-PLY",
                description="Plywood Board 1.2m x 2.4m",
                quantity_per=2.5,
                uom_code="PCS",
                scrap_pct=5.0,
                component_type="Item",
                position="Main Frame",
            ),
            BOMLine(
                line_no=20,
                component_item_no="RM-SCREW-M6",
                description="Screw M6x20mm Stainless Steel",
                quantity_per=24.0,
                uom_code="PCS",
                scrap_pct=2.0,
                component_type="Item",
                position="Assembly Hardware",
            ),
        ]
        
        bom = BOM(
            tenant_id=str(lab.id),
            item_no="FG-CHAIR-001",
            description="Dental Chair Complete Assembly",
            version_code="V1",
            base_uom="PCS",
            status="Certified",  # Already certified for testing
            certified_date=datetime.utcnow(),
            certified_by="seed_script",
            lines=bom_lines,
            created_by="seed_script",
            updated_by="seed_script",
        ).save()
        print(f"  ✅ Created BOM: {bom.item_no} {bom.version_code} - {bom.description}")
        print(f"     Status: {bom.status}, Lines: {len(bom.lines)}")
        for line in bom.lines:
            print(f"       {line.line_no}: {line.quantity_per} {line.uom_code} {line.component_item_no} (+{line.scrap_pct}% scrap)")
    
    # ========================================
    # 8. ROUTINGS
    # ========================================
    print("\n🛣️ Seeding Routings...")
    
    # Routing for FG-CHAIR-001
    existing_routing = Routing.objects(tenant_id=str(lab.id), item_no="FG-CHAIR-001", version_code="V1").first()
    if existing_routing:
        print(f"  ⏩ Routing 'RTG-CHAIR-001 V1' already exists")
    else:
        routing_operations = [
            RoutingOperation(
                operation_no=10,
                description="Cut and prepare wood components",
                work_center_code="MACHINING",
                machine_center_code="CNC-001",
                setup_time=30.0,
                run_time=8.0,
                wait_time=5.0,
                move_time=2.0,
                concurrent_capacities=1,
            ),
            RoutingOperation(
                operation_no=20,
                description="Assemble frame and components",
                work_center_code="ASSEMBLY",
                machine_center_code=None,
                setup_time=15.0,
                run_time=12.0,
                wait_time=5.0,
                move_time=5.0,
                concurrent_capacities=2,  # Can do 2 chairs in parallel
            ),
            RoutingOperation(
                operation_no=30,
                description="Paint and finishing",
                work_center_code="PAINT",
                machine_center_code=None,
                setup_time=20.0,
                run_time=15.0,
                wait_time=10.0,
                move_time=5.0,
                concurrent_capacities=1,
            ),
        ]
        
        routing = Routing(
            tenant_id=str(lab.id),
            item_no="FG-CHAIR-001",
            description="Dental Chair Manufacturing Process",
            version_code="V1",
            status="Certified",  # Already certified for testing
            certified_date=datetime.utcnow(),
            certified_by="seed_script",
            operations=routing_operations,
            created_by="seed_script",
            updated_by="seed_script",
        ).save()
        
        # Calculate total time
        total_setup = sum(op.setup_time for op in routing.operations)
        total_run = sum(op.run_time for op in routing.operations)
        
        print(f"  ✅ Created Routing: {routing.item_no} {routing.version_code} - {routing.description}")
        print(f"     Status: {routing.status}, Operations: {len(routing.operations)}")
        print(f"     Total time: {total_setup}min setup + {total_run}min run = {total_setup + total_run}min")
        for op in routing.operations:
            print(f"       Op {op.operation_no}: {op.description} @ {op.work_center_code}")
            print(f"         Setup: {op.setup_time}min, Run: {op.run_time}min, Concurrent: {op.concurrent_capacities}")
    
    # ========================================
    # 9. PRODUCTION ORDERS
    # ========================================
    print("\n📦 Seeding Production Orders...")
    
    # Get the certified BOM and Routing we just created
    bom = BOM.objects(tenant_id=str(lab.id), item_no="FG-CHAIR-001", version_code="V1", status="Certified").first()
    routing = Routing.objects(tenant_id=str(lab.id), item_no="FG-CHAIR-001", version_code="V1", status="Certified").first()
    
    production_orders_data = [
        {
            "order_no": "PO-2025-001",
            "item_no": "FG-CHAIR-001",
            "quantity": 10.0,
            "status": "Planned",
            "location_code": "MAIN",
            "due_date": datetime.utcnow() + timedelta(days=10),
        },
        {
            "order_no": "PO-2025-002",
            "item_no": "FG-CHAIR-001",
            "quantity": 5.0,
            "status": "Released",
            "location_code": "MAIN",
            "due_date": datetime.utcnow() + timedelta(days=5),
        },
    ]
    
    for po_data in production_orders_data:
        existing_po = ProductionOrder.objects(
            tenant_id=str(lab.id), 
            order_no=po_data["order_no"]
        ).first()
        
        if existing_po:
            print(f"  ⏩ Production Order '{po_data['order_no']}' already exists")
            continue
        
        # Calculate start date from due date (assuming 5 days lead time)
        start_date = po_data["due_date"] - timedelta(days=5)
        
        po = ProductionOrder(
            tenant_id=str(lab.id),
            order_no=po_data["order_no"],
            item_no=po_data["item_no"],
            description="Dental Chair Complete Assembly",
            quantity=po_data["quantity"],
            status=po_data["status"],
            location_code=po_data["location_code"],
            uom_code="PCS",
            start_date=start_date,
            due_date=po_data["due_date"],
            bom_no=bom.item_no if bom else None,
            bom_version_code=bom.version_code if bom else None,
            routing_no=routing.item_no if routing else None,
            routing_version_code=routing.version_code if routing else None,
            created_by="seed_script",
            updated_by="seed_script",
        ).save()
        
        status_emoji = "📅" if po.status == "Planned" else "🚀"
        print(f"  ✅ Created Production Order: {status_emoji} {po.order_no}")
        print(f"     Item: {po.item_no}, Qty: {po.quantity}, Status: {po.status}")
        print(f"     Start: {po.start_date.strftime('%Y-%m-%d')}, Due: {po.due_date.strftime('%Y-%m-%d')}")
    
    # ========================================
    # SUMMARY
    # ========================================
    print("\n" + "="*60)
    print("✅ Production Data Seeded Successfully!")
    print("="*60)
    
    print(f"\n📊 Master Data Summary:")
    print(f"   UOMs:      {UnitOfMeasure.objects(tenant_id=lab).count()}")
    print(f"   Locations: {Location.objects(tenant_id=lab).count()}")
    print(f"   Suppliers: {Supplier.objects(tenant_id=lab).count()}")
    print(f"   Items:     {Item.objects(tenant_id=lab).count()}")
    
    print(f"\n🏭 Core Production Summary:")
    print(f"   Work Centers:     {WorkCenter.objects(tenant_id=str(lab.id)).count()}")
    print(f"   Machine Centers:  {MachineCenter.objects(tenant_id=str(lab.id)).count()}")
    print(f"   BOMs:             {BOM.objects(tenant_id=str(lab.id)).count()}")
    print(f"   Routings:         {Routing.objects(tenant_id=str(lab.id)).count()}")
    print(f"   Production Orders: {ProductionOrder.objects(tenant_id=str(lab.id)).count()}")
    
    print(f"\n🎯 Test Scenarios:")
    print(f"   1. GET /api/production/masterdata/items → Should return 3 items")
    print(f"   2. GET /api/production/boms/certified/FG-CHAIR-001 → Should return V1 BOM")
    print(f"   3. GET /api/production/routings/certified/FG-CHAIR-001 → Should return V1 Routing")
    print(f"   4. GET /api/production/production-orders/by-status/Planned → Should return PO-2025-001")
    print(f"   5. POST /api/production/production-orders/{{id}}/release → Release PO-2025-001")
    print(f"   6. Create new Production Order → Should auto-explode BOM/Routing")
    print()


if __name__ == "__main__":
    seed_production_data()
