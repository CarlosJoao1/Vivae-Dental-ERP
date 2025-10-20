# backend/routes/production/production_orders.py
"""
Production Orders Routes - NAV/BC-style
Endpoints for managing production orders with BOM explosion and status workflow
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from mongoengine.errors import ValidationError, DoesNotExist, NotUniqueError
from typing import Tuple
from datetime import datetime, timedelta

from models.production import ProductionOrder, ProductionOrderLine, ProductionOrderRouting, BOM, Routing, Item, Location
from models.laboratory import Laboratory
from models.user import User
from services.permissions import ensure

bp = Blueprint("production_orders", __name__, url_prefix="/api/production/production-orders")

# ========================================
# HELPER FUNCTIONS (DRY pattern)
# ========================================

def _error_response(message: str, status: int = 400):
    """Standard error response"""
    return jsonify({"error": message}), status

def _not_found():
    """Standard 404 response"""
    return jsonify({"error": "Production Order not found"}), 404

def _validation_error(e: Exception):
    """Standard validation error response"""
    return jsonify({"error": f"Validation error: {str(e)}"}), 400

def _check_permission(lab, resource: str, action: str):
    """Check permission and return error response if denied"""
    uid = get_jwt_identity()
    user = None
    try:
        user = User.objects.get(id=uid)
    except Exception:
        user = User.objects(email=uid).first()
    if not user:
        return _error_response("User not found", 401)
    
    ensure(user, lab, resource, action)
    return None

def _get_lab() -> Laboratory:
    """Get laboratory from X-Tenant-Id header or JWT"""
    from flask import current_app
    from flask_jwt_extended import get_jwt
    
    # X-Tenant-Id header
    tenant_id = request.headers.get("X-Tenant-Id")
    if tenant_id and tenant_id != "default":
        try:
            return Laboratory.objects.get(id=tenant_id)
        except Exception as e:
            current_app.logger.warning("X-Tenant-Id inválido: %s", e)
    
    # JWT tenant_id
    claims = get_jwt() or {}
    tid = claims.get("tenant_id")
    try:
        if tid and tid != "default":
            return Laboratory.objects.get(id=tid)
    except Exception as e:
        current_app.logger.warning("tenant_id inválido no JWT: %s", e)
    
    # Fallback
    lab = Laboratory.objects.first()
    if not lab:
        lab = Laboratory(name="Default Lab").save()
    return lab

def _pagination() -> Tuple[int, int]:
    """Get pagination parameters from request"""
    page = max(1, int(request.args.get("page", 1) or 1))
    size = min(100, max(1, int(request.args.get("page_size", 50) or 50)))
    return page, size

def _query() -> str:
    """Get search query from request"""
    return (request.args.get("q", "") or "").strip()

def _explode_bom(bom: BOM, quantity: float, location_code: str) -> list:
    """
    Explode BOM into production order lines.
    
    Args:
        bom: BOM to explode
        quantity: Order quantity
        location_code: Default location for components
        
    Returns:
        List of ProductionOrderLine objects
    """
    lines = []
    
    for bom_line in bom.lines:
        # Calculate expected quantity considering scrap
        scrap_multiplier = 1.0 + (bom_line.scrap_pct / 100.0)
        expected_qty = bom_line.quantity_per * quantity * scrap_multiplier
        
        po_line = ProductionOrderLine(
            line_no=bom_line.line_no,
            component_item_no=bom_line.component_item_no,
            description=bom_line.description,
            quantity_per=bom_line.quantity_per,
            expected_quantity=expected_qty,
            consumed_quantity=0.0,
            remaining_quantity=expected_qty,
            uom_code=bom_line.uom_code,
            location_code=location_code,
            bom_line_no=bom_line.line_no,
            position=bom_line.position
        )
        lines.append(po_line)
    
    return lines

def _explode_routing(routing: Routing, quantity: float) -> list:
    """
    Explode Routing into production order routing lines.
    
    Args:
        routing: Routing to explode
        quantity: Order quantity
        
    Returns:
        List of ProductionOrderRouting objects
    """
    routing_lines = []
    
    for operation in routing.operations:
        # Calculate expected capacity need
        setup_time = operation.setup_time or 0.0
        run_time_per_unit = (operation.run_time or 0.0) / operation.concurrent_capacities
        total_run_time = run_time_per_unit * quantity
        expected_capacity = setup_time + total_run_time
        
        po_routing = ProductionOrderRouting(
            operation_no=operation.operation_no,
            work_center_code=operation.work_center_code,
            machine_center_code=operation.machine_center_code,
            description=operation.description,
            setup_time=setup_time,
            run_time=total_run_time,
            expected_capacity_need=expected_capacity,
            actual_setup_time=0.0,
            actual_run_time=0.0,
            remaining_time=expected_capacity,
            routing_operation_no=operation.operation_no,
            status="Planned"
        )
        routing_lines.append(po_routing)
    
    return routing_lines

# ========================================
# PRODUCTION ORDER ENDPOINTS
# ========================================

@bp.get("")
@jwt_required()
def production_order_list():
    """
    List all Production Orders with filters and pagination.
    
    Query params:
    - page: Page number (default 1)
    - page_size: Items per page (default 50, max 100)
    - q: Search by order_no or item_no
    - status: Filter by status
    - item_no: Filter by item
    - due_date_from: Filter by due date range (ISO format)
    - due_date_to: Filter by due date range (ISO format)
    """
    lab = _get_lab()
    perm_err = _check_permission(lab, 'production', 'read')
    if perm_err:
        return perm_err
    
    page, size = _pagination()
    q = _query()
    
    # Base query
    qs = ProductionOrder.objects(tenant_id=str(lab.id))
    
    # Search
    if q:
        qs = qs.filter(order_no__icontains=q) | ProductionOrder.objects(tenant_id=str(lab.id), item_no__icontains=q)
    
    # Filters
    if request.args.get("status"):
        qs = qs.filter(status=request.args["status"])
    
    if request.args.get("item_no"):
        qs = qs.filter(item_no=request.args["item_no"])
    
    if request.args.get("due_date_from"):
        try:
            date_from = datetime.fromisoformat(request.args["due_date_from"]).date()
            qs = qs.filter(due_date__gte=date_from)
        except ValueError:
            pass
    
    if request.args.get("due_date_to"):
        try:
            date_to = datetime.fromisoformat(request.args["due_date_to"]).date()
            qs = qs.filter(due_date__lte=date_to)
        except ValueError:
            pass
    
    # Pagination
    total = qs.count()
    items = qs.order_by("-due_date", "order_no").skip((page - 1) * size).limit(size)
    
    return jsonify({
        "total": total,
        "page": page,
        "page_size": size,
        "items": [po.to_dict() for po in items]
    }), 200

@bp.post("")
@jwt_required()
def production_order_create():
    """
    Create a new Production Order with BOM/Routing explosion.
    
    Body:
    {
        "order_no": "PO-2025-001",
        "item_no": "FG-CHAIR-001",
        "quantity": 100,
        "due_date": "2025-11-01",
        "location_code": "MAIN",
        "status": "Planned",
        "priority": 1
    }
    
    Auto-explodes certified BOM and Routing if available.
    """
    lab = _get_lab()
    perm_err = _check_permission(lab, 'production', 'create')
    if perm_err:
        return perm_err
    
    data = request.get_json()
    if not data:
        return _error_response("No data provided")
    
    # Validate required fields
    if not data.get("order_no"):
        return _error_response("order_no is required")
    if not data.get("item_no"):
        return _error_response("item_no is required")
    if not data.get("quantity"):
        return _error_response("quantity is required")
    
    # Verify item exists
    item = Item.objects(tenant_id=str(lab.id), item_no=data["item_no"]).first()
    if not item:
        return _error_response(f"Item {data['item_no']} not found", 404)
    
    # Verify item can be manufactured
    if item.item_type not in ["manufactured", "both"]:
        return _error_response(f"Item {data['item_no']} is not marked as manufactured")
    
    # Verify location exists
    location_code = data.get("location_code")
    if location_code:
        location = Location.objects(tenant_id=str(lab.id), code=location_code).first()
        if not location:
            return _error_response(f"Location {location_code} not found", 404)
    else:
        # Use default location
        location = Location.objects(tenant_id=str(lab.id), is_default=True).first()
        if location:
            location_code = location.code
    
    # Get certified BOM
    bom = BOM.objects(tenant_id=str(lab.id), item_no=data["item_no"], status="Certified").first()
    if not bom:
        return _error_response(f"No certified BOM found for item {data['item_no']}", 404)
    
    # Get certified Routing (optional)
    routing = Routing.objects(tenant_id=str(lab.id), item_no=data["item_no"], status="Certified").first()
    
    try:
        user_email = get_jwt_identity()
        quantity = float(data["quantity"])
        
        # Create Production Order
        po = ProductionOrder(
            tenant_id=str(lab.id),
            order_no=data["order_no"],
            description=data.get("description", f"Production Order for {item.description}"),
            item_no=data["item_no"],
            quantity=quantity,
            finished_quantity=0.0,
            remaining_quantity=quantity,
            uom_code=item.base_uom,
            location_code=location_code,
            status=data.get("status", "Planned"),
            priority=data.get("priority", 0),
            bom_no=bom.item_no,
            bom_version_code=bom.version_code,
            unit_cost=item.unit_cost or 0.0,
            created_by=user_email,
            updated_by=user_email
        )
        
        # Set dates
        if data.get("due_date"):
            try:
                po.due_date = datetime.fromisoformat(data["due_date"]).date()
            except ValueError:
                pass
        
        if data.get("start_date"):
            try:
                po.start_date = datetime.fromisoformat(data["start_date"]).date()
            except ValueError:
                pass
        elif po.due_date and item.lead_time_days:
            # Calculate start date from due date and lead time
            po.start_date = (datetime.combine(po.due_date, datetime.min.time()) - timedelta(days=item.lead_time_days)).date()
        
        # Explode BOM into lines
        po.lines = _explode_bom(bom, quantity, location_code)
        
        # Explode Routing into routing lines (if exists)
        if routing:
            po.routing_no = routing.item_no
            po.routing_version_code = routing.version_code
            po.routing_lines = _explode_routing(routing, quantity)
        
        po.save()
        
        return jsonify(po.to_dict()), 201
        
    except NotUniqueError:
        return _error_response(f"Production Order {data['order_no']} already exists", 409)
    except ValidationError as e:
        return _validation_error(e)
    except Exception as e:
        return _error_response(f"Error creating Production Order: {str(e)}", 500)

@bp.get("/<po_id>")
@jwt_required()
def production_order_get(po_id: str):
    """Get a single Production Order by ID"""
    lab = _get_lab()
    perm_err = _check_permission(lab, 'production', 'read')
    if perm_err:
        return perm_err
    
    try:
        po = ProductionOrder.objects.get(id=po_id, tenant_id=str(lab.id))
        return jsonify(po.to_dict()), 200
    except DoesNotExist:
        return _not_found()

@bp.patch("/<po_id>")
@jwt_required()
def production_order_update(po_id: str):
    """
    Update a Production Order.
    
    Business Rules:
    - Can only update if status is Simulated, Planned, or Firm Planned
    - Cannot update Released, Finished, or Cancelled orders
    """
    lab = _get_lab()
    perm_err = _check_permission(lab, 'production', 'update')
    if perm_err:
        return perm_err
    
    try:
        po = ProductionOrder.objects.get(id=po_id, tenant_id=str(lab.id))
    except DoesNotExist:
        return _not_found()
    
    # Business rule: Cannot update Released, Finished, or Cancelled orders
    if po.status in ["Released", "Finished", "Cancelled"]:
        return _error_response(f"Cannot update {po.status} Production Order", 403)
    
    data = request.get_json()
    if not data:
        return _error_response("No data provided")
    
    user_email = get_jwt_identity()
    
    try:
        # Update allowed fields
        if "description" in data:
            po.description = data["description"]
        if "quantity" in data:
            new_qty = float(data["quantity"])
            po.quantity = new_qty
            po.remaining_quantity = new_qty - po.finished_quantity
        if "due_date" in data:
            po.due_date = datetime.fromisoformat(data["due_date"]).date() if data["due_date"] else None
        if "start_date" in data:
            po.start_date = datetime.fromisoformat(data["start_date"]).date() if data["start_date"] else None
        if "location_code" in data:
            po.location_code = data["location_code"]
        if "priority" in data:
            po.priority = data["priority"]
        if "status" in data and data["status"] in ["Simulated", "Planned", "Firm Planned"]:
            po.status = data["status"]
        
        po.updated_by = user_email
        po.save()
        
        return jsonify(po.to_dict()), 200
        
    except ValidationError as e:
        return _validation_error(e)
    except Exception as e:
        return _error_response(f"Error updating Production Order: {str(e)}", 500)

@bp.delete("/<po_id>")
@jwt_required()
def production_order_delete(po_id: str):
    """
    Delete a Production Order.
    
    Business Rules:
    - Can only delete if status is Simulated or Planned
    - Cannot delete Firm Planned, Released, Finished, or Cancelled orders
    """
    lab = _get_lab()
    perm_err = _check_permission(lab, 'production', 'delete')
    if perm_err:
        return perm_err
    
    try:
        po = ProductionOrder.objects.get(id=po_id, tenant_id=str(lab.id))
    except DoesNotExist:
        return _not_found()
    
    # Business rule: Can only delete Simulated or Planned
    if po.status not in ["Simulated", "Planned"]:
        return _error_response(f"Cannot delete {po.status} Production Order. Only Simulated or Planned orders can be deleted.", 403)
    
    po.delete()
    return jsonify({"message": "Production Order deleted successfully"}), 200

@bp.post("/<po_id>/release")
@jwt_required()
def production_order_release(po_id: str):
    """
    Release a Production Order (start production).
    
    Business Rules:
    - Can only release from Planned or Firm Planned status
    - Creates component and capacity reservations
    - Changes status to Released
    """
    lab = _get_lab()
    perm_err = _check_permission(lab, 'production', 'update')
    if perm_err:
        return perm_err
    
    try:
        po = ProductionOrder.objects.get(id=po_id, tenant_id=str(lab.id))
    except DoesNotExist:
        return _not_found()
    
    # Business rule: Can only release from Planned or Firm Planned
    if po.status not in ["Planned", "Firm Planned"]:
        return _error_response(f"Cannot release {po.status} Production Order. Must be Planned or Firm Planned.", 403)
    
    user_email = get_jwt_identity()
    
    if po.release(user_email):
        return jsonify(po.to_dict()), 200
    else:
        return _error_response("Failed to release Production Order", 500)

@bp.post("/<po_id>/finish")
@jwt_required()
def production_order_finish(po_id: str):
    """
    Finish a Production Order (complete).
    
    Business Rules:
    - Can only finish from Released status
    - Verifies all quantities are posted
    - Changes status to Finished
    """
    lab = _get_lab()
    perm_err = _check_permission(lab, 'production', 'update')
    if perm_err:
        return perm_err
    
    try:
        po = ProductionOrder.objects.get(id=po_id, tenant_id=str(lab.id))
    except DoesNotExist:
        return _not_found()
    
    # Business rule: Can only finish from Released
    if po.status != "Released":
        return _error_response(f"Cannot finish {po.status} Production Order. Must be Released.", 403)
    
    user_email = get_jwt_identity()
    
    if po.finish(user_email):
        return jsonify(po.to_dict()), 200
    else:
        return _error_response("Cannot finish Production Order. Remaining quantity must be posted first.", 400)

@bp.post("/<po_id>/reopen")
@jwt_required()
def production_order_reopen(po_id: str):
    """
    Reopen a Finished Production Order (for corrections).
    
    Business Rules:
    - Can only reopen from Finished status
    - Used for posting corrections
    """
    lab = _get_lab()
    perm_err = _check_permission(lab, 'production', 'update')
    if perm_err:
        return perm_err
    
    try:
        po = ProductionOrder.objects.get(id=po_id, tenant_id=str(lab.id))
    except DoesNotExist:
        return _not_found()
    
    # Business rule: Can only reopen from Finished
    if po.status != "Finished":
        return _error_response(f"Cannot reopen {po.status} Production Order. Must be Finished.", 403)
    
    user_email = get_jwt_identity()
    
    if po.reopen(user_email):
        return jsonify(po.to_dict()), 200
    else:
        return _error_response("Failed to reopen Production Order", 500)

@bp.post("/<po_id>/cancel")
@jwt_required()
def production_order_cancel(po_id: str):
    """
    Cancel a Production Order.
    
    Business Rules:
    - Cannot cancel if status is Finished
    - Releases all reservations
    """
    lab = _get_lab()
    perm_err = _check_permission(lab, 'production', 'update')
    if perm_err:
        return perm_err
    
    try:
        po = ProductionOrder.objects.get(id=po_id, tenant_id=str(lab.id))
    except DoesNotExist:
        return _not_found()
    
    # Business rule: Cannot cancel if Finished
    if po.status == "Finished":
        return _error_response("Cannot cancel Finished Production Order.", 403)
    
    user_email = get_jwt_identity()
    
    if po.cancel(user_email):
        return jsonify(po.to_dict()), 200
    else:
        return _error_response("Failed to cancel Production Order", 500)

@bp.get("/by-item/<item_no>")
@jwt_required()
def production_orders_by_item(item_no: str):
    """Get all Production Orders for a specific item"""
    lab = _get_lab()
    perm_err = _check_permission(lab, 'production', 'read')
    if perm_err:
        return perm_err
    
    orders = ProductionOrder.objects(tenant_id=str(lab.id), item_no=item_no).order_by("-due_date")
    
    return jsonify({
        "item_no": item_no,
        "total": orders.count(),
        "orders": [po.to_dict() for po in orders]
    }), 200

@bp.get("/by-status/<status>")
@jwt_required()
def production_orders_by_status(status: str):
    """Get all Production Orders with specific status"""
    lab = _get_lab()
    perm_err = _check_permission(lab, 'production', 'read')
    if perm_err:
        return perm_err
    
    orders = ProductionOrder.objects(tenant_id=str(lab.id), status=status).order_by("-due_date")
    
    return jsonify({
        "status": status,
        "total": orders.count(),
        "orders": [po.to_dict() for po in orders]
    }), 200
