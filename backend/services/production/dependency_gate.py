"""
Dependency Gate Service

Validates that all required prerequisites exist before critical production operations.
This prevents runtime errors and provides clear guidance on missing setup.

Usage:
    from services.production import check_production_dependencies
    
    ok, checks = check_production_dependencies(laboratory)
    if not ok:
        return jsonify({"ok": False, "checks": checks}), 409

Critical operations that should call this:
- Creating a Production Order
- Releasing a Production Order
- Running MRP/MPS
- Exploding a BOM
"""

from typing import Tuple, List, Dict, Any
from models.production import UnitOfMeasure, Item, Location, Supplier
from models.laboratory import Laboratory


def check_production_dependencies(laboratory: Laboratory) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    Check if all production dependencies are configured.
    
    Args:
        laboratory: The Laboratory (tenant) to check
        
    Returns:
        Tuple of (all_ok: bool, checks: List[Dict])
        
        checks format:
        [
            {
                "resource": "Units of Measure",
                "status": "ok" | "warning" | "error",
                "message": "Human-readable message",
                "count": 5  # optional, number of resources found
            },
            ...
        ]
    """
    tenant_id = str(laboratory.id)
    checks = []
    all_ok = True
    
    # Check 1: At least one Unit of Measure exists
    uom_count = UnitOfMeasure.objects(tenant_id=tenant_id).count()
    if uom_count == 0:
        checks.append({
            "resource": "Units of Measure",
            "status": "error",
            "message": "No Units of Measure defined. Create at least one (e.g., PCS, KG, L).",
            "count": 0
        })
        all_ok = False
    else:
        checks.append({
            "resource": "Units of Measure",
            "status": "ok",
            "message": f"{uom_count} Unit(s) of Measure configured.",
            "count": uom_count
        })
    
    # Check 2: At least one Location exists and one is marked as default
    location_count = Location.objects(tenant_id=tenant_id).count()
    default_location = Location.objects(tenant_id=tenant_id, is_default=True).first()
    
    if location_count == 0:
        checks.append({
            "resource": "Locations",
            "status": "error",
            "message": "No Locations defined. Create at least one warehouse/location.",
            "count": 0
        })
        all_ok = False
    elif not default_location:
        checks.append({
            "resource": "Locations",
            "status": "warning",
            "message": f"{location_count} Location(s) exist, but none is marked as default. Mark one as default.",
            "count": location_count
        })
        # Warning doesn't block, so all_ok stays True
    else:
        checks.append({
            "resource": "Locations",
            "status": "ok",
            "message": f"{location_count} Location(s) configured, default is '{default_location.code}'.",
            "count": location_count
        })
    
    # Check 3: At least one Item exists
    item_count = Item.objects(tenant_id=tenant_id).count()
    manufactured_count = Item.objects(tenant_id=tenant_id, item_type__in=["manufactured", "both"]).count()
    purchased_count = Item.objects(tenant_id=tenant_id, item_type__in=["purchased", "both"]).count()
    
    if item_count == 0:
        checks.append({
            "resource": "Items",
            "status": "error",
            "message": "No Items defined. Create at least one Item (manufactured or purchased).",
            "count": 0
        })
        all_ok = False
    else:
        checks.append({
            "resource": "Items",
            "status": "ok",
            "message": f"{item_count} Item(s) configured ({manufactured_count} manufactured, {purchased_count} purchased).",
            "count": item_count
        })
    
    # Check 4: At least one Supplier exists (if there are purchased items)
    supplier_count = Supplier.objects(tenant_id=tenant_id).count()
    
    if purchased_count > 0 and supplier_count == 0:
        checks.append({
            "resource": "Suppliers",
            "status": "warning",
            "message": f"{purchased_count} purchased Item(s) exist, but no Suppliers defined. Create at least one Supplier.",
            "count": 0
        })
        # This is a warning, not blocking (user can proceed without suppliers)
    elif supplier_count > 0:
        checks.append({
            "resource": "Suppliers",
            "status": "ok",
            "message": f"{supplier_count} Supplier(s) configured.",
            "count": supplier_count
        })
    else:
        checks.append({
            "resource": "Suppliers",
            "status": "ok",
            "message": "No Suppliers needed (no purchased items).",
            "count": 0
        })
    
    # Check 5: BOMs exist for manufactured items (future check, placeholder)
    if manufactured_count > 0:
        # TODO: Uncomment when BOM model is implemented
        # bom_count = BOM.objects(tenant_id=tenant_id).count()
        # if bom_count == 0:
        #     checks.append({
        #         "resource": "Bills of Materials",
        #         "status": "warning",
        #         "message": f"{manufactured_count} manufactured Item(s) exist, but no BOMs defined.",
        #         "count": 0
        #     })
        # else:
        #     checks.append({
        #         "resource": "Bills of Materials",
        #         "status": "ok",
        #         "message": f"{bom_count} BOM(s) configured for manufactured items.",
        #         "count": bom_count
        #     })
        pass
    
    # Check 6: Routings exist for manufactured items (future check, placeholder)
    if manufactured_count > 0:
        # TODO: Uncomment when Routing model is implemented
        # routing_count = Routing.objects(tenant_id=tenant_id).count()
        # if routing_count == 0:
        #     checks.append({
        #         "resource": "Routings",
        #         "status": "warning",
        #         "message": f"{manufactured_count} manufactured Item(s) exist, but no Routings defined.",
        #         "count": 0
        #     })
        # else:
        #     checks.append({
        #         "resource": "Routings",
        #         "status": "ok",
        #         "message": f"{routing_count} Routing(s) configured for manufactured items.",
        #         "count": routing_count
        #     })
        pass
    
    return all_ok, checks


def check_item_can_be_manufactured(item: Item, laboratory: Laboratory) -> Tuple[bool, List[str]]:
    """
    Check if a specific item can be manufactured (has BOM, routing, etc).
    
    Args:
        item: The Item to check
        laboratory: The Laboratory (tenant)
        
    Returns:
        Tuple of (can_manufacture: bool, errors: List[str])
    """
    errors = []
    
    if item.item_type not in ["manufactured", "both"]:
        errors.append(f"Item {item.item_no} is not marked as manufactured.")
        return False, errors
    
    if not item.base_uom:
        errors.append(f"Item {item.item_no} has no base UOM defined.")
    
    # TODO: Uncomment when BOM model is implemented
    # tenant_id = str(laboratory.id)
    # bom = BOM.objects(tenant_id=tenant_id, item_no=item.item_no).first()
    # if not bom:
    #     errors.append(f"Item {item.item_no} has no BOM defined.")
    
    # TODO: Uncomment when Routing model is implemented
    # routing = Routing.objects(tenant_id=tenant_id, item_no=item.item_no).first()
    # if not routing:
    #     errors.append(f"Item {item.item_no} has no Routing defined.")
    
    return len(errors) == 0, errors


def check_item_can_be_purchased(item: Item, laboratory: Laboratory) -> Tuple[bool, List[str]]:
    """
    Check if a specific item can be purchased (has supplier, etc).
    
    Args:
        item: The Item to check
        laboratory: The Laboratory (tenant)
        
    Returns:
        Tuple of (can_purchase: bool, errors: List[str])
    """
    errors = []
    
    if item.item_type not in ["purchased", "both"]:
        errors.append(f"Item {item.item_no} is not marked as purchased.")
        return False, errors
    
    if not item.base_uom:
        errors.append(f"Item {item.item_no} has no base UOM defined.")
    
    tenant_id = str(laboratory.id)
    
    # Check if default supplier exists (if configured)
    if item.default_supplier_id:
        supplier = Supplier.objects(tenant_id=tenant_id, supplier_id=item.default_supplier_id).first()
        if not supplier:
            errors.append(f"Item {item.item_no} references non-existent supplier '{item.default_supplier_id}'.")
        elif supplier.status == "Blocked":
            errors.append(f"Item {item.item_no} default supplier '{item.default_supplier_id}' is blocked.")
    else:
        # No default supplier, check if at least one supplier exists
        supplier_count = Supplier.objects(tenant_id=tenant_id, status="Active").count()
        if supplier_count == 0:
            errors.append(f"Item {item.item_no} has no default supplier, and no active suppliers exist.")
    
    return len(errors) == 0, errors
