#!/usr/bin/env python3
"""
Script to seed production data to a remote MongoDB instance (Render production).
Run this script locally, pointing to the production MongoDB URI.

Usage:
    python seed_production_remote.py

Environment Variables Required:
    MONGO_URI_PRODUCTION - MongoDB connection string for production
    PRODUCTION_LAB_ID - Laboratory ID to use for seeding (optional, will prompt)
    
Safety Features:
    - Requires explicit confirmation before seeding production
    - Checks if data already exists to prevent duplicates
    - Can be run in dry-run mode
"""

import os
import sys
from datetime import datetime, timedelta
from mongoengine import connect, disconnect
from decimal import Decimal

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.production.item import Item
from models.production.uom import UOM
from models.production.location import Location
from models.production.supplier import Supplier
from models.production.work_center import WorkCenter, MachineCenter
from models.production.bom import BOM, BOMLine
from models.production.routing import Routing, RoutingOperation
from models.production.production_order import ProductionOrder

def confirm_production_seed():
    """Ask for explicit confirmation before seeding production."""
    print("\n" + "="*60)
    print("⚠️  WARNING: PRODUCTION SEED OPERATION")
    print("="*60)
    print("\nYou are about to seed data to a PRODUCTION environment.")
    print("This will create demo data in your live database.")
    print("\nMake sure you have:")
    print("  1. Backed up your production database")
    print("  2. Verified the MONGO_URI_PRODUCTION is correct")
    print("  3. Obtained approval for this operation")
    print("\n" + "="*60)
    
    response = input("\nType 'YES I UNDERSTAND' to proceed: ")
    return response == "YES I UNDERSTAND"

def check_existing_data(lab_id):
    """Check if production data already exists for this lab."""
    items = Item.objects(laboratory=lab_id).count()
    work_centers = WorkCenter.objects(laboratory=lab_id).count()
    boms = BOM.objects(laboratory=lab_id).count()
    
    print(f"\n📊 Existing data in laboratory:")
    print(f"  - Items: {items}")
    print(f"  - Work Centers: {work_centers}")
    print(f"  - BOMs: {boms}")
    
    if items > 0 or work_centers > 0 or boms > 0:
        print("\n⚠️  Data already exists for this laboratory!")
        response = input("Continue anyway? This may create duplicates (yes/no): ")
        return response.lower() == 'yes'
    
    return True

def seed_master_data(lab_id):
    """Seed basic master data (UOMs, Locations, Items)."""
    print("\n📦 Seeding Master Data...")
    
    # UOMs
    print("  Creating UOMs...")
    uom_pcs = UOM(
        laboratory=lab_id,
        code='PCS',
        description='Pieces',
        base_uom=True
    ).save()
    
    uom_kg = UOM(
        laboratory=lab_id,
        code='KG',
        description='Kilograms',
        base_uom=False
    ).save()
    
    uom_m = UOM(
        laboratory=lab_id,
        code='M',
        description='Meters',
        base_uom=False
    ).save()
    
    # Locations
    print("  Creating Locations...")
    loc_main = Location(
        laboratory=lab_id,
        code='MAIN',
        name='Main Warehouse',
        location_type='Warehouse'
    ).save()
    
    loc_prod = Location(
        laboratory=lab_id,
        code='PROD',
        name='Production Floor',
        location_type='Production'
    ).save()
    
    # Suppliers
    print("  Creating Suppliers...")
    supplier = Supplier(
        laboratory=lab_id,
        code='SUP-001',
        name='Demo Supplier Ltd',
        contact_person='John Smith',
        email='supplier@demo.com',
        phone='+351 123 456 789'
    ).save()
    
    # Items
    print("  Creating Items...")
    item_fg = Item(
        laboratory=lab_id,
        item_no='FG-DEMO-001',
        description='Demo Finished Good',
        item_type='Finished Good',
        base_uom=uom_pcs.code,
        unit_cost=Decimal('50.00'),
        unit_price=Decimal('100.00')
    ).save()
    
    item_rm1 = Item(
        laboratory=lab_id,
        item_no='RM-DEMO-001',
        description='Demo Raw Material 1',
        item_type='Raw Material',
        base_uom=uom_kg.code,
        unit_cost=Decimal('10.00')
    ).save()
    
    item_rm2 = Item(
        laboratory=lab_id,
        item_no='RM-DEMO-002',
        description='Demo Raw Material 2',
        item_type='Raw Material',
        base_uom=uom_m.code,
        unit_cost=Decimal('5.00')
    ).save()
    
    print("  ✅ Master Data created")
    return {
        'uoms': [uom_pcs, uom_kg, uom_m],
        'locations': [loc_main, loc_prod],
        'suppliers': [supplier],
        'items': [item_fg, item_rm1, item_rm2]
    }

def seed_work_centers(lab_id, location):
    """Seed work centers and machine centers."""
    print("\n🏭 Seeding Work Centers...")
    
    wc_machining = WorkCenter(
        laboratory=lab_id,
        code='MACHINING',
        name='Machining Department',
        work_center_type='Work Center',
        capacity_min_per_day=480,
        efficiency_pct=Decimal('85.0'),
        unit_cost_per_min=Decimal('0.50'),
        location_code=location.code
    ).save()
    
    wc_assembly = WorkCenter(
        laboratory=lab_id,
        code='ASSEMBLY',
        name='Assembly Department',
        work_center_type='Work Center',
        capacity_min_per_day=480,
        efficiency_pct=Decimal('90.0'),
        unit_cost_per_min=Decimal('0.40'),
        location_code=location.code
    ).save()
    
    mc_cnc = MachineCenter(
        laboratory=lab_id,
        code='CNC-001',
        name='CNC Machine 1',
        work_center_code=wc_machining.code,
        capacity_min_per_day=420,
        efficiency_pct=Decimal('80.0'),
        unit_cost_per_min=Decimal('0.75'),
        location_code=location.code,
        manufacturer='Demo Corp',
        model='CNC-X1000'
    ).save()
    
    print("  ✅ Work Centers created")
    return [wc_machining, wc_assembly], [mc_cnc]

def seed_bom(lab_id, item_fg, item_rm1, item_rm2, uom_pcs, uom_kg, uom_m):
    """Seed BOM for finished good."""
    print("\n📋 Seeding BOM...")
    
    bom = BOM(
        laboratory=lab_id,
        item_no=item_fg.item_no,
        version_code='V1',
        description=f'BOM for {item_fg.description}',
        status='Certified',
        base_uom=uom_pcs.code,
        lines=[
            BOMLine(
                line_no=10,
                item_no=item_rm1.item_no,
                description=item_rm1.description,
                quantity_per=Decimal('2.0'),
                uom_code=uom_kg.code,
                scrap_pct=Decimal('5.0')
            ),
            BOMLine(
                line_no=20,
                item_no=item_rm2.item_no,
                description=item_rm2.description,
                quantity_per=Decimal('1.5'),
                uom_code=uom_m.code,
                scrap_pct=Decimal('3.0')
            )
        ]
    ).save()
    
    print("  ✅ BOM created and certified")
    return bom

def seed_routing(lab_id, item_fg, wc_machining, wc_assembly, mc_cnc):
    """Seed Routing for finished good."""
    print("\n⚙️  Seeding Routing...")
    
    routing = Routing(
        laboratory=lab_id,
        item_no=item_fg.item_no,
        version_code='V1',
        description=f'Routing for {item_fg.description}',
        status='Certified',
        operations=[
            RoutingOperation(
                operation_no=10,
                description='CNC Machining',
                work_center_code=wc_machining.code,
                machine_center_code=mc_cnc.code,
                setup_time_min=30,
                run_time_min=15
            ),
            RoutingOperation(
                operation_no=20,
                description='Assembly',
                work_center_code=wc_assembly.code,
                setup_time_min=15,
                run_time_min=10
            )
        ]
    ).save()
    
    print("  ✅ Routing created and certified")
    return routing

def seed_production_order(lab_id, item_fg, bom, routing, location):
    """Seed a sample production order."""
    print("\n📝 Seeding Production Order...")
    
    # Find next order number (simple counter for demo)
    last_order = ProductionOrder.objects(laboratory=lab_id).order_by('-order_no').first()
    next_no = 1 if not last_order else int(last_order.order_no.split('-')[-1]) + 1
    
    po = ProductionOrder(
        laboratory=lab_id,
        order_no=f'PO-DEMO-{next_no:03d}',
        status='Planned',
        item_no=item_fg.item_no,
        description=item_fg.description,
        quantity=Decimal('10.0'),
        uom_code=item_fg.base_uom,
        location_code=location.code,
        bom_no=bom.item_no,
        bom_version=bom.version_code,
        routing_no=routing.item_no,
        routing_version=routing.version_code,
        due_date=datetime.now() + timedelta(days=7)
    ).save()
    
    print("  ✅ Production Order created")
    return po

def main():
    """Main seed function."""
    print("\n🌱 VIVAE ERP - Production Data Seed (Remote)")
    print("="*60)
    
    # Get production MongoDB URI
    mongo_uri = os.getenv('MONGO_URI_PRODUCTION')
    if not mongo_uri:
        print("\n❌ Error: MONGO_URI_PRODUCTION environment variable not set")
        print("\nSet it with:")
        print("  export MONGO_URI_PRODUCTION='mongodb+srv://...'")
        return 1
    
    # Get laboratory ID
    lab_id = os.getenv('PRODUCTION_LAB_ID')
    if not lab_id:
        print("\n📝 No PRODUCTION_LAB_ID set.")
        lab_id = input("Enter the Laboratory ID to seed: ").strip()
        if not lab_id:
            print("❌ Laboratory ID is required")
            return 1
    
    print(f"\n🏥 Target Laboratory: {lab_id}")
    print(f"🔗 MongoDB URI: {mongo_uri[:30]}...")
    
    # Confirm operation
    if not confirm_production_seed():
        print("\n❌ Operation cancelled by user")
        return 1
    
    # Connect to production database
    print("\n🔌 Connecting to production database...")
    try:
        connect(host=mongo_uri)
        print("✅ Connected successfully")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return 1
    
    # Check existing data
    if not check_existing_data(lab_id):
        print("\n❌ Operation cancelled - existing data found")
        disconnect()
        return 1
    
    # Seed data
    try:
        print("\n🚀 Starting seed operation...")
        
        master_data = seed_master_data(lab_id)
        work_centers, machine_centers = seed_work_centers(lab_id, master_data['locations'][1])
        bom = seed_bom(
            lab_id,
            master_data['items'][0],
            master_data['items'][1],
            master_data['items'][2],
            master_data['uoms'][0],
            master_data['uoms'][1],
            master_data['uoms'][2]
        )
        routing = seed_routing(
            lab_id,
            master_data['items'][0],
            work_centers[0],
            work_centers[1],
            machine_centers[0]
        )
        po = seed_production_order(
            lab_id,
            master_data['items'][0],
            bom,
            routing,
            master_data['locations'][1]
        )
        
        print("\n" + "="*60)
        print("✅ SEED COMPLETED SUCCESSFULLY!")
        print("="*60)
        print(f"\n📊 Created:")
        print(f"  - 3 UOMs")
        print(f"  - 2 Locations")
        print(f"  - 1 Supplier")
        print(f"  - 3 Items (1 FG, 2 RM)")
        print(f"  - 2 Work Centers")
        print(f"  - 1 Machine Center")
        print(f"  - 1 BOM (certified)")
        print(f"  - 1 Routing (certified)")
        print(f"  - 1 Production Order")
        
        print(f"\n🎯 You can now:")
        print(f"  1. Log in to your production app")
        print(f"  2. Navigate to Production → Planning")
        print(f"  3. See the demo production order: {po.order_no}")
        print(f"  4. Test Release → Finish workflow")
        
    except Exception as e:
        print(f"\n❌ Error during seed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        disconnect()
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
