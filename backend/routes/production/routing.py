# backend/routes/production/routing.py
"""
Routing Routes - NAV/BC-style
Endpoints for managing Routings with versioning and certification workflow
"""
from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from mongoengine.errors import ValidationError, DoesNotExist, NotUniqueError
from typing import Tuple

from models.production import Routing, RoutingOperation, Item, WorkCenter
from models.laboratory import Laboratory
from models.user import User
from .._authz import check_permission, require

bp = Blueprint("production_routing", __name__, url_prefix="/api/production/routings")

# ========================================
# HELPER FUNCTIONS (DRY pattern)
# ========================================

def _error_response(message: str, status: int = 400):
    """Standard error response"""
    return jsonify({"error": message}), status

def _not_found():
    """Standard 404 response"""
    return jsonify({"error": "Routing not found"}), 404

def _validation_error(e: Exception):
    """Standard validation error response"""
    return jsonify({"error": f"Validation error: {str(e)}"}), 400

## permission checks centralized in routes/_authz.py

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

# ========================================
# ROUTING ENDPOINTS
# ========================================

@bp.get("")
@jwt_required()
@require('read', get_lab=_get_lab)
def routing_list():
    """List all Routings with filters and pagination"""
    lab = g.lab
    # permission enforced by decorator
    
    page, size = _pagination()
    q = _query()
    
    # Base query
    qs = Routing.objects(tenant_id=str(lab.id))
    
    # Search
    if q:
        qs = qs.filter(item_no__icontains=q) | Routing.objects(tenant_id=str(lab.id), description__icontains=q)
    
    # Filters
    if request.args.get("item_no"):
        qs = qs.filter(item_no=request.args["item_no"])
    
    if request.args.get("status"):
        qs = qs.filter(status=request.args["status"])
    
    if request.args.get("version_code"):
        qs = qs.filter(version_code=request.args["version_code"])
    
    # Pagination
    total = qs.count()
    items = qs.order_by("item_no", "version_code").skip((page - 1) * size).limit(size)
    
    return jsonify({
        "total": total,
        "page": page,
        "page_size": size,
        "items": [routing.to_dict() for routing in items]
    }), 200

@bp.post("")
@jwt_required()
@require('create', get_lab=_get_lab)
def routing_create():
    """Create a new Routing"""
    lab = g.lab
    # permission enforced by decorator
    
    data = request.get_json()
    if not data:
        return _error_response("No data provided")
    
    # Validate required fields
    if not data.get("item_no"):
        return _error_response("item_no is required")
    
    # Verify item exists
    item = Item.objects(tenant_id=str(lab.id), item_no=data["item_no"]).first()
    if not item:
        return _error_response(f"Item {data['item_no']} not found", 404)
    
    # Verify item can be manufactured
    if item.item_type not in ["manufactured", "both"]:
        return _error_response(f"Item {data['item_no']} is not marked as manufactured or both")
    
    # Verify all work centers exist
    operations_data = data.get("operations", [])
    for op in operations_data:
        wc = WorkCenter.objects(tenant_id=str(lab.id), code=op.get("work_center_code")).first()
        if not wc:
            return _error_response(f"Work Center {op.get('work_center_code')} not found", 404)
    
    try:
        # Create Routing
        user_email = get_jwt_identity()
        
        routing = Routing(
            tenant_id=str(lab.id),
            item_no=data["item_no"],
            version_code=data.get("version_code", "V1"),
            description=data.get("description", ""),
            status=data.get("status", "New"),
            created_by=user_email,
            updated_by=user_email
        )
        
        # Add operations
        for op_data in operations_data:
            operation = RoutingOperation(
                operation_no=op_data["operation_no"],
                work_center_code=op_data["work_center_code"],
                machine_center_code=op_data.get("machine_center_code"),
                description=op_data.get("description", ""),
                setup_time=op_data.get("setup_time", 0.0),
                run_time=op_data.get("run_time", 0.0),
                wait_time=op_data.get("wait_time", 0.0),
                move_time=op_data.get("move_time", 0.0),
                concurrent_capacities=op_data.get("concurrent_capacities", 1),
                scrap_pct=op_data.get("scrap_pct", 0.0),
                routing_link_code=op_data.get("routing_link_code"),
                send_ahead_quantity=op_data.get("send_ahead_quantity", 0.0),
                is_subcontracted=op_data.get("is_subcontracted", False),
                subcontractor_id=op_data.get("subcontractor_id")
            )
            routing.operations.append(operation)
        
        routing.save()
        
        return jsonify(routing.to_dict()), 201
        
    except NotUniqueError:
        return _error_response(f"Routing for item {data['item_no']} version {data.get('version_code', 'V1')} already exists", 409)
    except ValidationError as e:
        return _validation_error(e)
    except Exception as e:
        return _error_response(f"Error creating Routing: {str(e)}", 500)

@bp.get("/<routing_id>")
@jwt_required()
@require('read', get_lab=_get_lab)
def routing_get(routing_id: str):
    """Get a single Routing by ID"""
    lab = g.lab
    # permission enforced by decorator
    
    try:
        routing = Routing.objects.get(id=routing_id, tenant_id=str(lab.id))
        return jsonify(routing.to_dict()), 200
    except DoesNotExist:
        return _not_found()

@bp.patch("/<routing_id>")
@jwt_required()
@require('update', get_lab=_get_lab)
def routing_update(routing_id: str):
    """Update a Routing (only if New or Under Development)"""
    lab = g.lab
    # permission enforced by decorator
    
    try:
        routing = Routing.objects.get(id=routing_id, tenant_id=str(lab.id))
    except DoesNotExist:
        return _not_found()
    
    # Business rule: Cannot update Certified or Closed Routings
    if routing.status in ["Certified", "Closed"]:
        return _error_response(f"Cannot update {routing.status} Routing. Create a new version instead.", 403)
    
    data = request.get_json()
    if not data:
        return _error_response("No data provided")
    
    user_email = get_jwt_identity()
    
    try:
        # Update allowed fields
        if "description" in data:
            routing.description = data["description"]
        if "status" in data and data["status"] in ["New", "Under Development"]:
            routing.status = data["status"]
        
        # Update operations if provided
        if "operations" in data:
            routing.operations = []
            for op_data in data["operations"]:
                # Verify work center exists
                wc = WorkCenter.objects(tenant_id=str(lab.id), code=op_data["work_center_code"]).first()
                if not wc:
                    return _error_response(f"Work Center {op_data['work_center_code']} not found", 404)
                
                operation = RoutingOperation(
                    operation_no=op_data["operation_no"],
                    work_center_code=op_data["work_center_code"],
                    machine_center_code=op_data.get("machine_center_code"),
                    description=op_data.get("description", ""),
                    setup_time=op_data.get("setup_time", 0.0),
                    run_time=op_data.get("run_time", 0.0),
                    wait_time=op_data.get("wait_time", 0.0),
                    move_time=op_data.get("move_time", 0.0),
                    concurrent_capacities=op_data.get("concurrent_capacities", 1),
                    scrap_pct=op_data.get("scrap_pct", 0.0),
                    routing_link_code=op_data.get("routing_link_code"),
                    send_ahead_quantity=op_data.get("send_ahead_quantity", 0.0),
                    is_subcontracted=op_data.get("is_subcontracted", False),
                    subcontractor_id=op_data.get("subcontractor_id")
                )
                routing.operations.append(operation)
        
        routing.updated_by = user_email
        routing.save()
        
        return jsonify(routing.to_dict()), 200
        
    except ValidationError as e:
        return _validation_error(e)
    except Exception as e:
        return _error_response(f"Error updating Routing: {str(e)}", 500)

@bp.delete("/<routing_id>")
@jwt_required()
@require('delete', get_lab=_get_lab)
def routing_delete(routing_id: str):
    """Delete a Routing (only if New)"""
    lab = g.lab
    # permission enforced by decorator
    
    try:
        routing = Routing.objects.get(id=routing_id, tenant_id=str(lab.id))
    except DoesNotExist:
        return _not_found()
    
    # Business rule: Can only delete New Routings
    if routing.status != "New":
        return _error_response(f"Cannot delete {routing.status} Routing. Only New Routings can be deleted.", 403)
    
    routing.delete()
    return jsonify({"message": "Routing deleted successfully"}), 200

@bp.post("/<routing_id>/certify")
@jwt_required()
@require('update', get_lab=_get_lab)
def routing_certify(routing_id: str):
    """Certify a Routing (make it active)"""
    lab = g.lab
    # permission enforced by decorator
    
    try:
        routing = Routing.objects.get(id=routing_id, tenant_id=str(lab.id))
    except DoesNotExist:
        return _not_found()
    
    # Business rule: Can only certify from Under Development
    if routing.status not in ["New", "Under Development"]:
        return _error_response(f"Cannot certify {routing.status} Routing. Must be New or Under Development.", 403)
    
    # Verify Routing has operations
    if not routing.operations:
        return _error_response("Cannot certify Routing with no operations", 400)
    
    user_email = get_jwt_identity()
    routing.certify(user_email)
    
    return jsonify(routing.to_dict()), 200

@bp.post("/<routing_id>/close")
@jwt_required()
@require('update', get_lab=_get_lab)
def routing_close(routing_id: str):
    """Close a Routing (archive)"""
    lab = g.lab
    # permission enforced by decorator
    
    try:
        routing = Routing.objects.get(id=routing_id, tenant_id=str(lab.id))
    except DoesNotExist:
        return _not_found()
    
    if routing.status == "Closed":
        return _error_response("Routing is already closed", 400)
    
    user_email = get_jwt_identity()
    routing.close(user_email)
    
    return jsonify(routing.to_dict()), 200

@bp.post("/<routing_id>/calculate-time")
@jwt_required()
@require('read', get_lab=_get_lab)
def routing_calculate_time(routing_id: str):
    """
    Calculate total production time for a given quantity.
    
    Query param:
    - quantity: Production quantity (required)
    
    Returns:
    {
        "quantity": 100,
        "setup_time_total": 60.0,
        "run_time_total": 200.0,
        "total_time": 260.0,
        "operations": [...]
    }
    """
    lab = g.lab
    # permission enforced by decorator
    
    try:
        routing = Routing.objects.get(id=routing_id, tenant_id=str(lab.id))
    except DoesNotExist:
        return _not_found()
    
    # Get quantity
    try:
        quantity = float(request.args.get("quantity", 1))
        if quantity <= 0:
            return _error_response("Quantity must be positive")
    except ValueError:
        return _error_response("Invalid quantity value")
    
    # Calculate time
    time_calc = routing.calculate_total_time(quantity)
    time_calc["quantity"] = quantity
    
    return jsonify(time_calc), 200

@bp.get("/by-item/<item_no>")
@jwt_required()
@require('read', get_lab=_get_lab)
def routing_by_item(item_no: str):
    """Get all Routing versions for a specific item"""
    lab = g.lab
    # permission enforced by decorator
    
    # Get all versions
    routings = Routing.objects(tenant_id=str(lab.id), item_no=item_no).order_by("-status", "version_code")
    
    return jsonify({
        "item_no": item_no,
        "total": routings.count(),
        "routings": [routing.to_dict() for routing in routings]
    }), 200

@bp.get("/certified/<item_no>")
@jwt_required()
@require('read', get_lab=_get_lab)
def routing_certified(item_no: str):
    """Get the certified (active) Routing for an item"""
    lab = _get_lab()
    # permission enforced by decorator
    
    routing = Routing.objects(tenant_id=str(lab.id), item_no=item_no, status="Certified").first()
    if not routing:
        return _error_response(f"No certified Routing found for item {item_no}", 404)
    
    return jsonify(routing.to_dict()), 200
