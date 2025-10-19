# backend/scripts/test_bom_explosion.py
"""
BOM Explosion Algorithm Tests

Tests multi-level explosion with:
1. Simple 2-level BOM (FG → Components)
2. Multi-level 3+ level BOM (FG → Sub-Assembly → Raw Materials)
3. Cycle detection (circular references)
4. Component consolidation (same component in multiple sub-assemblies)
5. Scrap calculation in cascade
"""

import os
import sys
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from mongoengine import connect
from models.production import BOM, BOMLine, Item
from models.laboratory import Laboratory
from services.production.bom_explosion import explode_bom

# ANSI color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def print_colored(message: str, color: str):
    """Print colored message"""
    print(f"{color}{message}{RESET}")


def setup_test_data():
    """
    Create test BOMs:
    
    Structure 1 (Simple):
    FG-TEST-001 (Finished Good)
    ├── RM-TEST-001 (Raw Material) x 2.0 (5% scrap)
    └── RM-TEST-002 (Raw Material) x 5.0 (10% scrap)
    
    Structure 2 (Multi-Level):
    FG-COMPLEX-001 (Finished Good)
    ├── SUB-FRAME-001 (Sub-Assembly) x 1.0 (5% scrap)
    │   ├── RM-WOOD-001 x 4.0 (3% scrap)
    │   └── RM-SCREW-001 x 12.0 (2% scrap)
    ├── SUB-COVER-001 (Sub-Assembly) x 2.0 (8% scrap)
    │   ├── RM-FABRIC-001 x 1.5 (10% scrap)
    │   └── RM-SCREW-001 x 8.0 (2% scrap) ← SAME as in SUB-FRAME
    └── RM-PAINT-001 x 0.5 (5% scrap)
    
    Structure 3 (Cycle Detection):
    FG-CYCLE-001 (Finished Good)
    └── SUB-CYCLE-001 (Sub-Assembly)
        └── FG-CYCLE-001 (loops back!)
    """
    print_colored("\nSetting up test data...", BLUE)
    
    # Get tenant
    lab = Laboratory.objects.first()
    if not lab:
        print_colored("❌ No laboratory found!", RED)
        sys.exit(1)
    
    tenant_id = str(lab.id)
    
    # Clean existing test data (use upsert strategy to avoid duplicates)
    Item.objects(tenant_id=tenant_id, item_no__startswith="FG-TEST").delete()
    Item.objects(tenant_id=tenant_id, item_no__startswith="FG-COMPLEX").delete()
    Item.objects(tenant_id=tenant_id, item_no__startswith="FG-CYCLE").delete()
    Item.objects(tenant_id=tenant_id, item_no__startswith="SUB-").delete()
    Item.objects(tenant_id=tenant_id, item_no__startswith="RM-TEST").delete()
    Item.objects(tenant_id=tenant_id, item_no="RM-WOOD-001").delete()
    Item.objects(tenant_id=tenant_id, item_no="RM-FABRIC-001").delete()
    Item.objects(tenant_id=tenant_id, item_no="RM-SCREW-001").delete()
    Item.objects(tenant_id=tenant_id, item_no="RM-PAINT-001").delete()
    
    BOM.objects(tenant_id=tenant_id, item_no__startswith="FG-TEST").delete()
    BOM.objects(tenant_id=tenant_id, item_no__startswith="FG-COMPLEX").delete()
    BOM.objects(tenant_id=tenant_id, item_no__startswith="FG-CYCLE").delete()
    BOM.objects(tenant_id=tenant_id, item_no__startswith="SUB-").delete()
    
    # Create items
    items_data = [
        # Test 1: Simple
        {"item_no": "FG-TEST-001", "description": "Simple Test FG", "item_type": "manufactured"},
        {"item_no": "RM-TEST-001", "description": "Test RM 1", "item_type": "purchased"},
        {"item_no": "RM-TEST-002", "description": "Test RM 2", "item_type": "purchased"},
        
        # Test 2: Multi-Level
        {"item_no": "FG-COMPLEX-001", "description": "Complex Multi-Level FG", "item_type": "manufactured"},
        {"item_no": "SUB-FRAME-001", "description": "Frame Sub-Assembly", "item_type": "manufactured"},
        {"item_no": "SUB-COVER-001", "description": "Cover Sub-Assembly", "item_type": "manufactured"},
        {"item_no": "RM-WOOD-001", "description": "Wood Plank", "item_type": "purchased"},
        {"item_no": "RM-FABRIC-001", "description": "Fabric Roll", "item_type": "purchased"},
        {"item_no": "RM-SCREW-001", "description": "Screw M6", "item_type": "purchased"},
        {"item_no": "RM-PAINT-001", "description": "Paint Liter", "item_type": "purchased"},
        
        # Test 3: Cycle
        {"item_no": "FG-CYCLE-001", "description": "Cycle Test FG", "item_type": "manufactured"},
        {"item_no": "SUB-CYCLE-001", "description": "Cycle Sub-Assembly", "item_type": "manufactured"},
    ]
    
    for item_data in items_data:
        Item(
            tenant_id=tenant_id,
            item_no=item_data["item_no"],
            description=item_data["description"],
            item_type=item_data["item_type"],
            base_uom="PCS",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        ).save()
    
    print_colored(f"✅ Created {len(items_data)} test items", GREEN)
    
    # Create BOMs
    # BOM 1: Simple (FG-TEST-001)
    BOM(
        tenant_id=tenant_id,
        item_no="FG-TEST-001",
        version_code="V1",
        status="Certified",
        base_uom="PCS",
        lines=[
            BOMLine(
                line_no=10,
                component_item_no="RM-TEST-001",
                description="Test RM 1",
                quantity_per=2.0,
                uom_code="PCS",
                scrap_pct=5.0,
                component_type="Item",
                position="MAIN"
            ),
            BOMLine(
                line_no=20,
                component_item_no="RM-TEST-002",
                description="Test RM 2",
                quantity_per=5.0,
                uom_code="PCS",
                scrap_pct=10.0,
                component_type="Item",
                position="MAIN"
            ),
        ],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    ).save()
    
    # BOM 2: Sub-Assembly Frame
    BOM(
        tenant_id=tenant_id,
        item_no="SUB-FRAME-001",
        version_code="V1",
        status="Certified",
        base_uom="PCS",
        lines=[
            BOMLine(
                line_no=10,
                component_item_no="RM-WOOD-001",
                description="Wood Plank",
                quantity_per=4.0,
                uom_code="PCS",
                scrap_pct=3.0,
                component_type="Item",
                position="FRAME"
            ),
            BOMLine(
                line_no=20,
                component_item_no="RM-SCREW-001",
                description="Screw M6",
                quantity_per=12.0,
                uom_code="PCS",
                scrap_pct=2.0,
                component_type="Item",
                position="FRAME"
            ),
        ],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    ).save()
    
    # BOM 3: Sub-Assembly Cover
    BOM(
        tenant_id=tenant_id,
        item_no="SUB-COVER-001",
        version_code="V1",
        status="Certified",
        base_uom="PCS",
        lines=[
            BOMLine(
                line_no=10,
                component_item_no="RM-FABRIC-001",
                description="Fabric Roll",
                quantity_per=1.5,
                uom_code="M",
                scrap_pct=10.0,
                component_type="Item",
                position="COVER"
            ),
            BOMLine(
                line_no=20,
                component_item_no="RM-SCREW-001",  # Same screw as frame!
                description="Screw M6",
                quantity_per=8.0,
                uom_code="PCS",
                scrap_pct=2.0,
                component_type="Item",
                position="COVER"
            ),
        ],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    ).save()
    
    # BOM 4: Complex FG (references sub-assemblies)
    BOM(
        tenant_id=tenant_id,
        item_no="FG-COMPLEX-001",
        version_code="V1",
        status="Certified",
        base_uom="PCS",
        lines=[
            BOMLine(
                line_no=10,
                component_item_no="SUB-FRAME-001",
                description="Frame Sub-Assembly",
                quantity_per=1.0,
                uom_code="PCS",
                scrap_pct=5.0,
                component_type="Item",
                position="ASSEMBLY"
            ),
            BOMLine(
                line_no=20,
                component_item_no="SUB-COVER-001",
                description="Cover Sub-Assembly",
                quantity_per=2.0,
                uom_code="PCS",
                scrap_pct=8.0,
                component_type="Item",
                position="ASSEMBLY"
            ),
            BOMLine(
                line_no=30,
                component_item_no="RM-PAINT-001",
                description="Paint Liter",
                quantity_per=0.5,
                uom_code="L",
                scrap_pct=5.0,
                component_type="Item",
                position="FINISH"
            ),
        ],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    ).save()
    
    # BOM 5: Cycle (FG-CYCLE-001 → SUB-CYCLE-001 → FG-CYCLE-001)
    BOM(
        tenant_id=tenant_id,
        item_no="FG-CYCLE-001",
        version_code="V1",
        status="Certified",
        base_uom="PCS",
        lines=[
            BOMLine(
                line_no=10,
                component_item_no="SUB-CYCLE-001",
                description="Cycle Sub-Assembly",
                quantity_per=1.0,
                uom_code="PCS",
                scrap_pct=0.0,
                component_type="Item",
                position="MAIN"
            ),
        ],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    ).save()
    
    BOM(
        tenant_id=tenant_id,
        item_no="SUB-CYCLE-001",
        version_code="V1",
        status="Certified",
        base_uom="PCS",
        lines=[
            BOMLine(
                line_no=10,
                component_item_no="FG-CYCLE-001",  # Loops back!
                description="Cycle Test FG",
                quantity_per=1.0,
                uom_code="PCS",
                scrap_pct=0.0,
                component_type="Item",
                position="MAIN"
            ),
        ],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    ).save()
    
    print_colored("✅ Created 6 test BOMs (3 scenarios)", GREEN)
    print_colored("   - Simple 2-level BOM", BLUE)
    print_colored("   - Complex 3-level BOM with consolidation", BLUE)
    print_colored("   - Cycle detection BOM", BLUE)
    
    return tenant_id


def test_simple_explosion(tenant_id: str):
    """Test 1: Simple 2-level BOM explosion"""
    print("\nTEST 1: Simple 2-Level BOM Explosion")
    print("=" * 60)
    
    result = explode_bom(tenant_id, "FG-TEST-001", quantity=10.0)
    
    print(f"Item: {result.item_no} - {result.description}")
    print(f"Quantity: {result.quantity}")
    print(f"Status: {result.status}")
    print(f"Max Level: {result.max_level}")
    print(f"Components: {len(result.components)}")
    print(f"Consolidated Components: {len(result.consolidated_components)}")
    
    # Expected:
    # RM-TEST-001: 2.0 * 10 * 1.05 (5% scrap) = 21.0
    # RM-TEST-002: 5.0 * 10 * 1.10 (10% scrap) = 55.0
    
    for comp in result.consolidated_components.values():
        print(f"  {comp.item_no}: {comp.total_quantity:.2f} {comp.uom_code} (scrap: {comp.scrap_pct}%)")
    
    # Assertions
    assert result.status == "success", "Should succeed"
    assert len(result.consolidated_components) == 2, "Should have 2 components"
    
    rm1_qty = result.consolidated_components["RM-TEST-001"].total_quantity
    rm2_qty = result.consolidated_components["RM-TEST-002"].total_quantity
    
    assert abs(rm1_qty - 21.0) < 0.01, f"RM-TEST-001 qty incorrect: expected 21.0, got {rm1_qty}"
    assert abs(rm2_qty - 55.0) < 0.01, f"RM-TEST-002 qty incorrect: expected 55.0, got {rm2_qty}"
    
    print_colored("✅ TEST 1 PASSED", GREEN)


def test_multi_level_explosion(tenant_id: str):
    """Test 2: Multi-level BOM with consolidation"""
    print("\nTEST 2: Multi-Level BOM with Consolidation")
    print("=" * 60)
    
    result = explode_bom(tenant_id, "FG-COMPLEX-001", quantity=5.0)
    
    print(f"Item: {result.item_no} - {result.description}")
    print(f"Quantity: {result.quantity}")
    print(f"Status: {result.status}")
    print(f"Max Level: {result.max_level}")
    print(f"Components: {len(result.components)}")
    print(f"Consolidated Components: {len(result.consolidated_components)}")
    
    # Expected consolidation:
    # RM-SCREW-001 appears in both SUB-FRAME and SUB-COVER
    # From SUB-FRAME: 12 * 1.0 * 5 * 1.05 * 1.02 = 64.26
    # From SUB-COVER: 8 * 2.0 * 5 * 1.08 * 1.02 = 88.128
    # Total: 152.388
    
    for comp in result.consolidated_components.values():
        print(f"  {comp.item_no}: {comp.total_quantity:.2f} {comp.uom_code} (level {comp.level}, sources: {', '.join(comp.source_boms)})")
    
    # Debug: Print all components with levels
    print("\nAll components:")
    for comp in result.components:
        print(f"  Level {comp.level}: {comp.item_no} x {comp.total_quantity:.2f}")
    
    # Assertions
    assert result.status == "success", "Should succeed"
    assert result.max_level >= 2, f"Should have at least 2 levels, got {result.max_level}"
    
    # Check consolidation of RM-SCREW-001
    screw = result.consolidated_components.get("RM-SCREW-001")
    assert screw is not None, "RM-SCREW-001 should be in components"
    assert len(screw.source_boms) == 2, "RM-SCREW-001 should come from 2 BOMs"
    assert screw.total_quantity > 150, f"RM-SCREW-001 qty too low: {screw.total_quantity}"
    
    print_colored("✅ TEST 2 PASSED (Consolidation works!)", GREEN)


def test_cycle_detection(tenant_id: str):
    """Test 3: Cycle detection"""
    print("\nTEST 3: Cycle Detection")
    print("=" * 60)
    
    result = explode_bom(tenant_id, "FG-CYCLE-001", quantity=1.0)
    
    print(f"Item: {result.item_no} - {result.description}")
    print(f"Quantity: {result.quantity}")
    print(f"Status: {result.status}")
    print(f"Has Cycles: {result.has_cycles}")
    print(f"Cycles Detected: {result.cycles_detected}")
    print(f"Messages: {result.messages}")
    
    # Assertions
    assert result.has_cycles, "Should detect cycle"
    assert "FG-CYCLE-001" in result.cycles_detected, "Should list FG-CYCLE-001 in cycles"
    assert result.status == "warning", "Status should be warning"
    assert any("Cycle detected" in msg for msg in result.messages), "Should have cycle message"
    
    print_colored("✅ TEST 3 PASSED (Cycle detected!)", GREEN)


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("BOM EXPLOSION ALGORITHM - TEST SUITE")
    print("=" * 60)
    
    # Connect to MongoDB
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/vivae_dental_erp")
    connect(host=mongo_uri)
    print_colored(f"✅ Connected to MongoDB: {mongo_uri}", GREEN)
    
    # Setup
    tenant_id = setup_test_data()
    
    # Run tests
    try:
        test_simple_explosion(tenant_id)
        test_multi_level_explosion(tenant_id)
        test_cycle_detection(tenant_id)
        
        print_colored("\n" + "=" * 60, GREEN)
        print_colored("ALL TESTS PASSED!", GREEN)
        print_colored("=" * 60, GREEN)
        
    except AssertionError as e:
        print_colored(f"\n❌ TEST FAILED: {str(e)}", RED)
        sys.exit(1)
    except Exception as e:
        print_colored(f"\n❌ UNEXPECTED ERROR: {str(e)}", RED)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
