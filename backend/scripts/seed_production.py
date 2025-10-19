# backend/scripts/seed_production.py
"""
Seed Production Master Data (NAV/BC-style)
Creates minimal seed data for production module testing

Seeds:
- 5 UOMs: PCS, KG, L, H, BOX
- 1 Location: MAIN (default)
- 1 Supplier: SUP-ABC (lead time 2 days)
- 3 Items: FG-CHAIR (manufactured), RM-WOOD, RM-SCREW (purchased)
"""
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mongoengine import connect
from models.laboratory import Laboratory
from models.production import UnitOfMeasure, Item, Location, Supplier
from config.db import get_mongo_uri


def seed_production_data():
    """Seed production master data"""
    
    # Connect to database
    mongo_uri = get_mongo_uri()
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
    # SUMMARY
    # ========================================
    print("\n" + "="*60)
    print("✅ Production Master Data Seeded Successfully!")
    print("="*60)
    
    print(f"\n📊 Summary:")
    print(f"   UOMs:      {UnitOfMeasure.objects(tenant_id=lab).count()}")
    print(f"   Locations: {Location.objects(tenant_id=lab).count()}")
    print(f"   Suppliers: {Supplier.objects(tenant_id=lab).count()}")
    print(f"   Items:     {Item.objects(tenant_id=lab).count()}")
    
    print(f"\n🎯 Next Steps:")
    print(f"   1. Register blueprint in app.py: from routes.production import masterdata_bp")
    print(f"   2. Test endpoints: GET /api/production/masterdata/items")
    print(f"   3. Create BOM for FG-CHAIR-001 with RM-WOOD-PLY and RM-SCREW-M6")
    print(f"   4. Implement Dependency Gate service")
    print()


if __name__ == "__main__":
    seed_production_data()
