# backend/scripts/seed_production_enhanced.py
"""
ENHANCED Production Seed Script - Complex Multi-Level BOM Hierarchies

This script creates a comprehensive production environment with:
- 12 items (3 finished goods, 4 semi-finished, 5 raw materials)
- Multi-level BOMs (3 levels deep)
- Complex routing operations
- 5 work centers, 4 machine centers
- 8 production orders in various statuses
- Realistic lead times, costs, and capacities

Hierarchy Example:
FG-DENTAL-UNIT (Level 0 - Finished Good)
├── SF-CHAIR-001 (Level 1 - Semi-Finished)
│   ├── RM-WOOD-PLY (Level 2 - Raw Material)
│   ├── RM-FOAM-HD (Level 2 - Raw Material)
│   └── RM-FABRIC (Level 2 - Raw Material)
├── SF-BASE-001 (Level 1 - Semi-Finished)
│   ├── RM-STEEL-TUBE (Level 2 - Raw Material)
│   └── RM-PAINT (Level 2 - Raw Material)
└── RM-SCREW-M6 (Level 1 - Raw Material)
"""
import sys
import os
from datetime import datetime, timedelta
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mongoengine import connect
from models.laboratory import Laboratory
from models.production import (
    UnitOfMeasure, Item, Location, Supplier,
    WorkCenter, MachineCenter, BOM, BOMLine, Routing, RoutingOperation, ProductionOrder
)


def seed_enhanced_production():
    """Seed comprehensive production data with multi-level BOMs"""
    
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/vivae_dental_erp")
    connect(host=mongo_uri)
    
    print("🌱 ENHANCED Production Seeding - Multi-Level BOMs & Complex Scenarios")
    print("="*70)
    
    lab = Laboratory.objects.first()
    if not lab:
        lab = Laboratory(name="Demo Dental Lab", active=True).save()
    print(f"📍 Laboratory: {lab.name}\n")
    
    # ========================================
    # 1. UOMS (Extended)
    # ========================================
    print("📏 Seeding Units of Measure...")
    uoms_data = [
        {"code": "PCS", "description": "Pieces", "decimals": 0},
        {"code": "KG", "description": "Kilograms", "decimals": 3},
        {"code": "L", "description": "Liters", "decimals": 3},
        {"code": "M", "description": "Meters", "decimals": 2},
        {"code": "M2", "description": "Square Meters", "decimals": 3},
        {"code": "H", "description": "Hours", "decimals": 2},
        {"code": "MIN", "description": "Minutes", "decimals": 2},
        {"code": "BOX", "description": "Boxes", "decimals": 0},
        {"code": "SET", "description": "Sets", "decimals": 0},
    ]
    
    for uom_data in uoms_data:
        if not UnitOfMeasure.objects(tenant_id=lab, code=uom_data["code"]).first():
            UnitOfMeasure(tenant_id=lab, **uom_data, created_by="seed_enhanced", updated_by="seed_enhanced").save()
            print(f"  ✅ UOM: {uom_data['code']}")
        else:
            print(f"  ⏩ UOM '{uom_data['code']}' exists")
    
    # ========================================
    # 2. LOCATIONS (Multiple)
    # ========================================
    print("\n📦 Seeding Locations...")
    locations_data = [
        {"code": "MAIN", "name": "Main Warehouse", "city": "Porto", "postal_code": "4000-123", "is_default": True},
        {"code": "PROD", "name": "Production Floor", "city": "Porto", "postal_code": "4000-124", "is_default": False},
        {"code": "QC", "name": "Quality Control", "city": "Porto", "postal_code": "4000-125", "is_default": False},
    ]
    
    for loc_data in locations_data:
        if not Location.objects(tenant_id=lab, code=loc_data["code"]).first():
            Location(
                tenant_id=lab,
                code=loc_data["code"],
                name=loc_data["name"],
                address="Industrial Zone, Building 3",
                city=loc_data["city"],
                postal_code=loc_data["postal_code"],
                country_code="PT",
                allow_negative_stock=False,
                is_default=loc_data["is_default"],
                blocked=False,
                created_by="seed_enhanced",
                updated_by="seed_enhanced"
            ).save()
            print(f"  ✅ Location: {loc_data['code']} - {loc_data['name']}")
        else:
            print(f"  ⏩ Location '{loc_data['code']}' exists")
    
    # ========================================
    # 3. SUPPLIERS (Multiple)
    # ========================================
    print("\n🏭 Seeding Suppliers...")
    suppliers_data = [
        {"id": "SUP-WOOD", "name": "WoodCraft Supplies Ltd.", "lead_time": 3, "rating": "A"},
        {"id": "SUP-METAL", "name": "MetalWorks Industries", "lead_time": 5, "rating": "A"},
        {"id": "SUP-FAB", "name": "Premium Fabrics Co.", "lead_time": 2, "rating": "B"},
        {"id": "SUP-CHEM", "name": "Chemical Solutions Inc.", "lead_time": 7, "rating": "B"},
    ]
    
    for sup_data in suppliers_data:
        if not Supplier.objects(tenant_id=lab, supplier_id=sup_data["id"]).first():
            Supplier(
                tenant_id=lab,
                supplier_id=sup_data["id"],
                name=sup_data["name"],
                address="Supplier Street",
                city="Lisbon",
                postal_code="1000-001",
                country_code="PT",
                phone_no=f"+351 21 {random.randint(100,999)} {random.randint(1000,9999)}",
                email=f"orders@{sup_data['id'].lower().replace('sup-','')}.pt",
                lead_time_days_default=sup_data["lead_time"],
                currency_code="EUR",
                rating=sup_data["rating"],
                status="Active",
                preferred_supplier=sup_data["rating"] == "A",
                created_by="seed_enhanced",
                updated_by="seed_enhanced"
            ).save()
            print(f"  ✅ Supplier: {sup_data['id']} - {sup_data['name']} ({sup_data['lead_time']} days)")
        else:
            print(f"  ⏩ Supplier '{sup_data['id']}' exists")
    
    # ========================================
    # 4. ITEMS (12 total: 3 FG, 4 SF, 5 RM)
    # ========================================
    print("\n📦 Seeding Items (Multi-Level Hierarchy)...")
    
    items_data = [
        # === FINISHED GOODS (Level 0) ===
        {
            "item_no": "FG-DENTAL-UNIT",
            "description": "Complete Dental Treatment Unit",
            "item_type": "manufactured",
            "base_uom": "PCS",
            "lead_time_days": 10,
            "safety_stock_qty": 1,
            "reorder_point": 3,
            "unit_cost": 5500.00,
            "critical_item": True,
        },
        {
            "item_no": "FG-CHAIR-001",
            "description": "Dental Chair Complete Assembly",
            "item_type": "manufactured",
            "base_uom": "PCS",
            "lead_time_days": 5,
            "safety_stock_qty": 2,
            "reorder_point": 5,
            "unit_cost": 1500.00,
            "critical_item": True,
        },
        {
            "item_no": "FG-LIGHT-001",
            "description": "LED Dental Light System",
            "item_type": "manufactured",
            "base_uom": "PCS",
            "lead_time_days": 3,
            "safety_stock_qty": 3,
            "unit_cost": 800.00,
        },
        
        # === SEMI-FINISHED (Level 1) ===
        {
            "item_no": "SF-CHAIR-001",
            "description": "Chair Frame Assembly (Semi-Finished)",
            "item_type": "semi-finished",
            "base_uom": "PCS",
            "lead_time_days": 3,
            "safety_stock_qty": 5,
            "unit_cost": 600.00,
        },
        {
            "item_no": "SF-BASE-001",
            "description": "Hydraulic Base Assembly (Semi-Finished)",
            "item_type": "semi-finished",
            "base_uom": "PCS",
            "lead_time_days": 4,
            "safety_stock_qty": 4,
            "unit_cost": 400.00,
        },
        {
            "item_no": "SF-LIGHT-HEAD",
            "description": "LED Light Head Assembly",
            "item_type": "semi-finished",
            "base_uom": "PCS",
            "lead_time_days": 2,
            "safety_stock_qty": 6,
            "unit_cost": 350.00,
        },
        {
            "item_no": "SF-ARM-001",
            "description": "Articulated Arm Assembly",
            "item_type": "semi-finished",
            "base_uom": "PCS",
            "lead_time_days": 2,
            "safety_stock_qty": 8,
            "unit_cost": 280.00,
        },
        
        # === RAW MATERIALS (Level 2) ===
        {
            "item_no": "RM-WOOD-PLY",
            "description": "Plywood Board 1.2m x 2.4m",
            "item_type": "purchased",
            "base_uom": "PCS",
            "default_supplier_id": "SUP-WOOD",
            "lead_time_days": 3,
            "safety_stock_qty": 20,
            "reorder_point": 30,
            "unit_cost": 25.50,
        },
        {
            "item_no": "RM-STEEL-TUBE",
            "description": "Steel Tube 50mm Diameter",
            "item_type": "purchased",
            "base_uom": "M",
            "default_supplier_id": "SUP-METAL",
            "lead_time_days": 5,
            "safety_stock_qty": 50,
            "unit_cost": 12.80,
        },
        {
            "item_no": "RM-FABRIC",
            "description": "Medical Grade Fabric (Leather Alternative)",
            "item_type": "purchased",
            "base_uom": "M2",
            "default_supplier_id": "SUP-FAB",
            "lead_time_days": 2,
            "safety_stock_qty": 30,
            "unit_cost": 35.00,
        },
        {
            "item_no": "RM-PAINT",
            "description": "Industrial Paint White RAL9010",
            "item_type": "purchased",
            "base_uom": "L",
            "default_supplier_id": "SUP-CHEM",
            "lead_time_days": 7,
            "safety_stock_qty": 10,
            "unit_cost": 18.50,
        },
        {
            "item_no": "RM-SCREW-M6",
            "description": "Screw M6x20mm Stainless Steel",
            "item_type": "purchased",
            "base_uom": "PCS",
            "default_supplier_id": "SUP-METAL",
            "lead_time_days": 2,
            "safety_stock_qty": 1000,
            "unit_cost": 0.15,
        },
    ]
    
    for item_data in items_data:
        if not Item.objects(tenant_id=lab, item_no=item_data["item_no"]).first():
            Item(
                tenant_id=lab,
                item_no=item_data["item_no"],
                description=item_data["description"],
                item_type=item_data["item_type"],
                base_uom=item_data["base_uom"],
                default_supplier_id=item_data.get("default_supplier_id"),
                lead_time_days=item_data["lead_time_days"],
                safety_stock_qty=item_data["safety_stock_qty"],
                reorder_point=item_data.get("reorder_point"),
                reorder_quantity=item_data.get("reorder_quantity", item_data["safety_stock_qty"] * 3),
                unit_cost=item_data["unit_cost"],
                costing_method="standard",
                status="Active",
                critical_item=item_data.get("critical_item", False),
                created_by="seed_enhanced",
                updated_by="seed_enhanced"
            ).save()
            type_emoji = "🏭" if item_data["item_type"] == "manufactured" else ("🔧" if item_data["item_type"] == "semi-finished" else "📦")
            print(f"  ✅ {type_emoji} {item_data['item_no']}: {item_data['description'][:50]}")
        else:
            print(f"  ⏩ Item '{item_data['item_no']}' exists")
    
    # ========================================
    # 5. WORK CENTERS (5 Total)
    # ========================================
    print("\n🏭 Seeding Work Centers...")
    
    work_centers_data = [
        {"code": "CUT", "name": "Cutting Department", "capacity": 480, "efficiency": 90, "cost": 0.30, "overhead": 28},
        {"code": "WELD", "name": "Welding Department", "capacity": 480, "efficiency": 85, "cost": 0.35, "overhead": 32},
        {"code": "ASSEMBLY", "name": "Assembly Department", "capacity": 480, "efficiency": 85, "cost": 0.25, "overhead": 25},
        {"code": "PAINT", "name": "Paint & Finishing", "capacity": 240, "efficiency": 75, "cost": 0.20, "overhead": 20},
        {"code": "QC", "name": "Quality Control", "capacity": 480, "efficiency": 95, "cost": 0.18, "overhead": 15},
    ]
    
    for wc_data in work_centers_data:
        if not WorkCenter.objects(tenant_id=str(lab.id), code=wc_data["code"]).first():
            WorkCenter(
                tenant_id=str(lab.id),
                code=wc_data["code"],
                name=wc_data["name"],
                description=f"{wc_data['name']} - Production line",
                location_code="PROD",
                capacity=wc_data["capacity"],
                efficiency_pct=wc_data["efficiency"],
                unit_cost=wc_data["cost"],
                overhead_rate=wc_data["overhead"],
                blocked=False,
                created_by="seed_enhanced",
                updated_by="seed_enhanced"
            ).save()
            print(f"  ✅ WC: {wc_data['code']} - {wc_data['name']} ({wc_data['capacity']}min, {wc_data['efficiency']}%)")
        else:
            print(f"  ⏩ Work Center '{wc_data['code']}' exists")
    
    # ========================================
    # 6. MACHINE CENTERS (4 Total)
    # ========================================
    print("\n⚙️ Seeding Machine Centers...")
    
    machine_centers_data = [
        {"code": "CNC-001", "name": "CNC Milling Machine #1", "wc": "CUT", "capacity": 480, "efficiency": 92, "cost": 0.42, "overhead": 35},
        {"code": "SAW-001", "name": "Band Saw Machine #1", "wc": "CUT", "capacity": 480, "efficiency": 88, "cost": 0.28, "overhead": 22},
        {"code": "WELD-001", "name": "TIG Welding Station #1", "wc": "WELD", "capacity": 480, "efficiency": 87, "cost": 0.38, "overhead": 30},
        {"code": "SPRAY-001", "name": "Spray Paint Booth #1", "wc": "PAINT", "capacity": 240, "efficiency": 75, "cost": 0.25, "overhead": 18},
    ]
    
    for mc_data in machine_centers_data:
        if not MachineCenter.objects(tenant_id=str(lab.id), code=mc_data["code"]).first():
            MachineCenter(
                tenant_id=str(lab.id),
                code=mc_data["code"],
                name=mc_data["name"],
                description=f"{mc_data['name']} for precision work",
                work_center_code=mc_data["wc"],
                location_code="PROD",
                capacity=mc_data["capacity"],
                efficiency_pct=mc_data["efficiency"],
                unit_cost=mc_data["cost"],
                overhead_rate=mc_data["overhead"],
                blocked=False,
                created_by="seed_enhanced",
                updated_by="seed_enhanced"
            ).save()
            print(f"  ✅ MC: {mc_data['code']} @ {mc_data['wc']} ({mc_data['efficiency']}%)")
        else:
            print(f"  ⏩ Machine Center '{mc_data['code']}' exists")
    
    # ========================================
    # 7. BOMS (Multi-Level Hierarchy)
    # ========================================
    print("\n📋 Seeding BOMs (Multi-Level)...")
    
    # Level 2: SF-CHAIR-001 (Semi-Finished)
    if not BOM.objects(tenant_id=str(lab.id), item_no="SF-CHAIR-001", version_code="V1").first():
        bom = BOM(
            tenant_id=str(lab.id),
            item_no="SF-CHAIR-001",
            description="Chair Frame Assembly",
            version_code="V1",
            base_uom="PCS",
            status="Certified",
            certified_date=datetime.utcnow(),
            certified_by="seed_enhanced",
            lines=[
                BOMLine(line_no=10, component_item_no="RM-WOOD-PLY", description="Plywood", quantity_per=2.5, uom_code="PCS", scrap_pct=5, component_type="Item", position="Frame"),
                BOMLine(line_no=20, component_item_no="RM-FABRIC", description="Fabric", quantity_per=1.2, uom_code="M2", scrap_pct=8, component_type="Item", position="Cushion"),
                BOMLine(line_no=30, component_item_no="RM-SCREW-M6", description="Screws", quantity_per=16, uom_code="PCS", scrap_pct=2, component_type="Item", position="Assembly"),
            ],
            created_by="seed_enhanced",
            updated_by="seed_enhanced"
        ).save()
        print(f"  ✅ BOM: SF-CHAIR-001 V1 (3 lines, Level 2)")
    
    # Level 2: SF-BASE-001 (Semi-Finished)
    if not BOM.objects(tenant_id=str(lab.id), item_no="SF-BASE-001", version_code="V1").first():
        bom = BOM(
            tenant_id=str(lab.id),
            item_no="SF-BASE-001",
            description="Hydraulic Base Assembly",
            version_code="V1",
            base_uom="PCS",
            status="Certified",
            certified_date=datetime.utcnow(),
            certified_by="seed_enhanced",
            lines=[
                BOMLine(line_no=10, component_item_no="RM-STEEL-TUBE", description="Steel Tube", quantity_per=4.5, uom_code="M", scrap_pct=3, component_type="Item", position="Base Structure"),
                BOMLine(line_no=20, component_item_no="RM-PAINT", description="Paint", quantity_per=0.8, uom_code="L", scrap_pct=10, component_type="Item", position="Finishing"),
                BOMLine(line_no=30, component_item_no="RM-SCREW-M6", description="Screws", quantity_per=12, uom_code="PCS", scrap_pct=2, component_type="Item", position="Assembly"),
            ],
            created_by="seed_enhanced",
            updated_by="seed_enhanced"
        ).save()
        print(f"  ✅ BOM: SF-BASE-001 V1 (3 lines, Level 2)")
    
    # Level 1: FG-CHAIR-001 (uses SF items)
    if not BOM.objects(tenant_id=str(lab.id), item_no="FG-CHAIR-001", version_code="V1").first():
        bom = BOM(
            tenant_id=str(lab.id),
            item_no="FG-CHAIR-001",
            description="Dental Chair Complete Assembly",
            version_code="V1",
            base_uom="PCS",
            status="Certified",
            certified_date=datetime.utcnow(),
            certified_by="seed_enhanced",
            lines=[
                BOMLine(line_no=10, component_item_no="SF-CHAIR-001", description="Chair Frame Assembly", quantity_per=1, uom_code="PCS", scrap_pct=0, component_type="Item", position="Main Assembly"),
                BOMLine(line_no=20, component_item_no="SF-BASE-001", description="Hydraulic Base", quantity_per=1, uom_code="PCS", scrap_pct=0, component_type="Item", position="Base"),
                BOMLine(line_no=30, component_item_no="RM-SCREW-M6", description="Final Assembly Screws", quantity_per=24, uom_code="PCS", scrap_pct=2, component_type="Item", position="Final Assembly"),
            ],
            created_by="seed_enhanced",
            updated_by="seed_enhanced"
        ).save()
        print(f"  ✅ BOM: FG-CHAIR-001 V1 (3 lines, Level 1 - uses 2 SF items)")
    
    # Level 0: FG-DENTAL-UNIT (top-level, uses FG-CHAIR-001)
    if not BOM.objects(tenant_id=str(lab.id), item_no="FG-DENTAL-UNIT", version_code="V1").first():
        bom = BOM(
            tenant_id=str(lab.id),
            item_no="FG-DENTAL-UNIT",
            description="Complete Dental Treatment Unit",
            version_code="V1",
            base_uom="PCS",
            status="Certified",
            certified_date=datetime.utcnow(),
            certified_by="seed_enhanced",
            lines=[
                BOMLine(line_no=10, component_item_no="FG-CHAIR-001", description="Dental Chair", quantity_per=1, uom_code="PCS", scrap_pct=0, component_type="Item", position="Chair Unit"),
                BOMLine(line_no=20, component_item_no="SF-LIGHT-HEAD", description="LED Light", quantity_per=1, uom_code="PCS", scrap_pct=0, component_type="Item", position="Light Unit"),
                BOMLine(line_no=30, component_item_no="SF-ARM-001", description="Articulated Arm", quantity_per=2, uom_code="PCS", scrap_pct=0, component_type="Item", position="Arms"),
            ],
            created_by="seed_enhanced",
            updated_by="seed_enhanced"
        ).save()
        print(f"  ✅ BOM: FG-DENTAL-UNIT V1 (3 lines, Level 0 - MULTI-LEVEL!)")
    
    print("\n  📊 BOM Hierarchy:")
    print("     FG-DENTAL-UNIT (L0)")
    print("     ├── FG-CHAIR-001 (L1)")
    print("     │   ├── SF-CHAIR-001 (L2)")
    print("     │   │   ├── RM-WOOD-PLY")
    print("     │   │   ├── RM-FABRIC")
    print("     │   │   └── RM-SCREW-M6")
    print("     │   ├── SF-BASE-001 (L2)")
    print("     │   │   ├── RM-STEEL-TUBE")
    print("     │   │   ├── RM-PAINT")
    print("     │   │   └── RM-SCREW-M6")
    print("     │   └── RM-SCREW-M6")
    print("     ├── SF-LIGHT-HEAD")
    print("     └── SF-ARM-001 (x2)")
    
    # ========================================
    # 8. ROUTINGS
    # ========================================
    print("\n🛣️ Seeding Routings...")
    
    # Routing for SF-CHAIR-001
    if not Routing.objects(tenant_id=str(lab.id), item_no="SF-CHAIR-001", version_code="V1").first():
        Routing(
            tenant_id=str(lab.id),
            item_no="SF-CHAIR-001",
            description="Chair Frame Manufacturing",
            version_code="V1",
            status="Certified",
            certified_date=datetime.utcnow(),
            certified_by="seed_enhanced",
            operations=[
                RoutingOperation(operation_no=10, description="Cut wood panels", work_center_code="CUT", machine_center_code="SAW-001", setup_time=20, run_time=6, wait_time=5, move_time=2, concurrent_capacities=1),
                RoutingOperation(operation_no=20, description="Assemble frame", work_center_code="ASSEMBLY", setup_time=15, run_time=10, wait_time=5, move_time=3, concurrent_capacities=2),
                RoutingOperation(operation_no=30, description="QC inspection", work_center_code="QC", setup_time=0, run_time=5, wait_time=0, move_time=2, concurrent_capacities=1),
            ],
            created_by="seed_enhanced",
            updated_by="seed_enhanced"
        ).save()
        print(f"  ✅ Routing: SF-CHAIR-001 V1 (3 operations)")
    
    # Routing for SF-BASE-001
    if not Routing.objects(tenant_id=str(lab.id), item_no="SF-BASE-001", version_code="V1").first():
        Routing(
            tenant_id=str(lab.id),
            item_no="SF-BASE-001",
            description="Hydraulic Base Manufacturing",
            version_code="V1",
            status="Certified",
            certified_date=datetime.utcnow(),
            certified_by="seed_enhanced",
            operations=[
                RoutingOperation(operation_no=10, description="Cut steel tubes", work_center_code="CUT", machine_center_code="SAW-001", setup_time=25, run_time=8, wait_time=5, move_time=3, concurrent_capacities=1),
                RoutingOperation(operation_no=20, description="Weld base structure", work_center_code="WELD", machine_center_code="WELD-001", setup_time=30, run_time=15, wait_time=10, move_time=5, concurrent_capacities=1),
                RoutingOperation(operation_no=30, description="Paint & dry", work_center_code="PAINT", machine_center_code="SPRAY-001", setup_time=20, run_time=12, wait_time=15, move_time=5, concurrent_capacities=1),
                RoutingOperation(operation_no=40, description="Final inspection", work_center_code="QC", setup_time=0, run_time=8, wait_time=0, move_time=2, concurrent_capacities=1),
            ],
            created_by="seed_enhanced",
            updated_by="seed_enhanced"
        ).save()
        print(f"  ✅ Routing: SF-BASE-001 V1 (4 operations)")
    
    # Routing for FG-CHAIR-001
    if not Routing.objects(tenant_id=str(lab.id), item_no="FG-CHAIR-001", version_code="V1").first():
        Routing(
            tenant_id=str(lab.id),
            item_no="FG-CHAIR-001",
            description="Dental Chair Final Assembly",
            version_code="V1",
            status="Certified",
            certified_date=datetime.utcnow(),
            certified_by="seed_enhanced",
            operations=[
                RoutingOperation(operation_no=10, description="Assemble chair & base", work_center_code="ASSEMBLY", setup_time=15, run_time=12, wait_time=5, move_time=5, concurrent_capacities=2),
                RoutingOperation(operation_no=20, description="Install hydraulics", work_center_code="ASSEMBLY", setup_time=10, run_time=18, wait_time=5, move_time=3, concurrent_capacities=1),
                RoutingOperation(operation_no=30, description="Final QC & test", work_center_code="QC", setup_time=0, run_time=15, wait_time=0, move_time=5, concurrent_capacities=1),
            ],
            created_by="seed_enhanced",
            updated_by="seed_enhanced"
        ).save()
        print(f"  ✅ Routing: FG-CHAIR-001 V1 (3 operations)")
    
    # Routing for FG-DENTAL-UNIT
    if not Routing.objects(tenant_id=str(lab.id), item_no="FG-DENTAL-UNIT", version_code="V1").first():
        Routing(
            tenant_id=str(lab.id),
            item_no="FG-DENTAL-UNIT",
            description="Complete Unit Final Assembly",
            version_code="V1",
            status="Certified",
            certified_date=datetime.utcnow(),
            certified_by="seed_enhanced",
            operations=[
                RoutingOperation(operation_no=10, description="Integrate all components", work_center_code="ASSEMBLY", setup_time=20, run_time=30, wait_time=10, move_time=10, concurrent_capacities=1),
                RoutingOperation(operation_no=20, description="Install electronics & wiring", work_center_code="ASSEMBLY", setup_time=15, run_time=25, wait_time=5, move_time=5, concurrent_capacities=1),
                RoutingOperation(operation_no=30, description="Full system testing", work_center_code="QC", setup_time=0, run_time=45, wait_time=0, move_time=10, concurrent_capacities=1),
            ],
            created_by="seed_enhanced",
            updated_by="seed_enhanced"
        ).save()
        print(f"  ✅ Routing: FG-DENTAL-UNIT V1 (3 operations)")
    
    # ========================================
    # 9. PRODUCTION ORDERS (8 orders)
    # ========================================
    print("\n📦 Seeding Production Orders (Various Statuses)...")
    
    po_data = [
        {"no": "PO-2025-001", "item": "FG-DENTAL-UNIT", "qty": 2, "status": "Planned", "days_offset": 15},
        {"no": "PO-2025-002", "item": "FG-CHAIR-001", "qty": 10, "status": "Released", "days_offset": 5},
        {"no": "PO-2025-003", "item": "FG-CHAIR-001", "qty": 5, "status": "Finished", "days_offset": -3},
        {"no": "PO-2025-004", "item": "SF-CHAIR-001", "qty": 15, "status": "Released", "days_offset": 3},
        {"no": "PO-2025-005", "item": "SF-BASE-001", "qty": 20, "status": "Planned", "days_offset": 8},
        {"no": "PO-2025-006", "item": "FG-LIGHT-001", "qty": 8, "status": "Planned", "days_offset": 10},
        {"no": "PO-2025-007", "item": "FG-CHAIR-001", "qty": 3, "status": "Cancelled", "days_offset": 0},
        {"no": "PO-2025-008", "item": "SF-ARM-001", "qty": 25, "status": "Released", "days_offset": 4},
    ]
    
    for po in po_data:
        if not ProductionOrder.objects(tenant_id=str(lab.id), order_no=po["no"]).first():
            item = Item.objects(tenant_id=lab, item_no=po["item"]).first()
            bom = BOM.objects(tenant_id=str(lab.id), item_no=po["item"], status="Certified").first()
            routing = Routing.objects(tenant_id=str(lab.id), item_no=po["item"], status="Certified").first()
            
            due_date = datetime.utcnow() + timedelta(days=po["days_offset"])
            start_date = due_date - timedelta(days=item.lead_time_days if item else 5)
            
            po_obj = ProductionOrder(
                tenant_id=str(lab.id),
                order_no=po["no"],
                item_no=po["item"],
                description=item.description if item else po["item"],
                quantity=po["qty"],
                status=po["status"],
                location_code="MAIN",
                uom_code=item.base_uom if item else "PCS",
                start_date=start_date.date(),
                due_date=due_date.date(),
                bom_no=bom.item_no if bom else None,
                bom_version_code=bom.version_code if bom else None,
                routing_no=routing.item_no if routing else None,
                routing_version_code=routing.version_code if routing else None,
                created_by="seed_enhanced",
                updated_by="seed_enhanced"
            )
            
            # Simulate finished orders
            if po["status"] == "Finished":
                po_obj.finished_quantity = po["qty"]
                po_obj.remaining_quantity = 0
                po_obj.finished_date = datetime.utcnow()
                po_obj.finished_by = "seed_enhanced"
                po_obj.end_date = datetime.utcnow().date()
            elif po["status"] == "Released":
                po_obj.released_date = datetime.utcnow() - timedelta(days=1)
                po_obj.released_by = "seed_enhanced"
            
            po_obj.save()
            
            status_emoji = {"Planned": "📅", "Released": "🚀", "Finished": "✅", "Cancelled": "❌"}[po["status"]]
            print(f"  {status_emoji} PO: {po['no']} - {po['item']} (Qty: {po['qty']}, Status: {po['status']})")
        else:
            print(f"  ⏩ PO '{po['no']}' exists")
    
    # ========================================
    # SUMMARY
    # ========================================
    print("\n" + "="*70)
    print("✅ ENHANCED Production Data Seeded Successfully!")
    print("="*70)
    
    print(f"\n📊 Summary:")
    print(f"   UOMs:              {UnitOfMeasure.objects(tenant_id=lab).count()}")
    print(f"   Locations:         {Location.objects(tenant_id=lab).count()}")
    print(f"   Suppliers:         {Supplier.objects(tenant_id=lab).count()}")
    print(f"   Items:             {Item.objects(tenant_id=lab).count()}")
    print(f"     - Finished Goods:    {Item.objects(tenant_id=lab, item_type='manufactured').count()}")
    print(f"     - Semi-Finished:     {Item.objects(tenant_id=lab, item_type='semi-finished').count()}")
    print(f"     - Raw Materials:     {Item.objects(tenant_id=lab, item_type='purchased').count()}")
    print(f"   Work Centers:      {WorkCenter.objects(tenant_id=str(lab.id)).count()}")
    print(f"   Machine Centers:   {MachineCenter.objects(tenant_id=str(lab.id)).count()}")
    print(f"   BOMs:              {BOM.objects(tenant_id=str(lab.id)).count()}")
    print(f"   Routings:          {Routing.objects(tenant_id=str(lab.id)).count()}")
    print(f"   Production Orders: {ProductionOrder.objects(tenant_id=str(lab.id)).count()}")
    
    print(f"\n🎯 Key Features:")
    print(f"   ✅ Multi-Level BOM (3 levels deep)")
    print(f"   ✅ Complex item hierarchies (FG → SF → RM)")
    print(f"   ✅ Multiple work centers & machines")
    print(f"   ✅ Various PO statuses (Planned, Released, Finished, Cancelled)")
    print(f"   ✅ Realistic lead times & costs")
    print()


if __name__ == "__main__":
    seed_enhanced_production()
