# backend/routes/production/bom.py
"""
BOM (Bill of Materials) Routes - NAV/BC-style
Endpoints for managing BOMs with versioning and certification workflow
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from mongoengine.errors import ValidationError, DoesNotExist, NotUniqueError
from typing import Tuple

from models.production import BOM, BOMLine, Item
from models.laboratory import Laboratory
from models.user import User
from services.permissions import ensure
from services.production.bom_explosion import explode_bom

bp = Blueprint("production_bom", __name__, url_prefix="/api/production/boms")

# ========================================
# HELPER FUNCTIONS (DRY pattern)
# ========================================

def _error_response(message: str, status: int = 400):
    """Standard error response"""
    return jsonify({"error": message}), status

def _not_found():
    """Standard 404 response"""
    return jsonify({"error": "BOM not found"}), 404

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
    
    ensure(lab, user, resource, action)
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

# ========================================
# BOM ENDPOINTS
# ========================================

@bp.get("")
@jwt_required()
def bom_list():
    """
    List all BOMs with filters and pagination.
    
    Query params:
    - page: Page number (default 1)
    - page_size: Items per page (default 50, max 100)
    - q: Search by item_no or description
    - item_no: Filter by item
    - status: Filter by status (New, Under Development, Certified, Closed)
    - version_code: Filter by version
    """
    lab = _get_lab()
    perm_err = _check_permission(lab, 'production', 'read')
    if perm_err:
        return perm_err
    
    page, size = _pagination()
    q = _query()
    
    # Base query
    qs = BOM.objects(tenant_id=str(lab.id))
    
    # Search
    if q:
        qs = qs.filter(item_no__icontains=q) | BOM.objects(tenant_id=str(lab.id), description__icontains=q)
    
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
        "items": [bom.to_dict() for bom in items]
    }), 200

@bp.post("")
@jwt_required()
def bom_create():
    """
    Create a new BOM.
    
    Body:
    {
        "item_no": "FG-CHAIR-001",
        "version_code": "V1",
        "description": "Chair Assembly BOM",
        "status": "New",
        "base_quantity": 1.0,
        "base_uom": "PCS",
        "is_phantom": false,
        "lines": [
            {
                "line_no": 10,
                "component_item_no": "RM-WOOD-PLY",
                "description": "Wood Plywood",
                "quantity_per": 2.5,
                "uom_code": "KG",
                "scrap_pct": 5.0,
                "position": "Frame"
            }
        ]
    }
    """
    lab = _get_lab()
    perm_err = _check_permission(lab, 'production', 'create')
    if perm_err:
        return perm_err
    
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
    
    # Verify all component items exist
    lines_data = data.get("lines", [])
    for line in lines_data:
        comp_item = Item.objects(tenant_id=str(lab.id), item_no=line.get("component_item_no")).first()
        if not comp_item:
            return _error_response(f"Component item {line.get('component_item_no')} not found", 404)
    
    try:
        # Create BOM
        user_email = get_jwt_identity()
        
        bom = BOM(
            tenant_id=str(lab.id),
            item_no=data["item_no"],
            version_code=data.get("version_code", "V1"),
            description=data.get("description", ""),
            status=data.get("status", "New"),
            base_quantity=data.get("base_quantity", 1.0),
            base_uom=data.get("base_uom", item.base_uom),
            is_phantom=data.get("is_phantom", False),
            production_lead_time_days=data.get("production_lead_time_days"),
            created_by=user_email,
            updated_by=user_email
        )
        
        # Add lines
        for line_data in lines_data:
            line = BOMLine(
                line_no=line_data["line_no"],
                component_type=line_data.get("component_type", "Item"),
                component_item_no=line_data["component_item_no"],
                description=line_data.get("description", ""),
                quantity_per=line_data["quantity_per"],
                uom_code=line_data.get("uom_code"),
                scrap_pct=line_data.get("scrap_pct", 0.0),
                position=line_data.get("position"),
                position_2=line_data.get("position_2"),
                position_3=line_data.get("position_3"),
                routing_link_code=line_data.get("routing_link_code"),
                lead_time_offset=line_data.get("lead_time_offset", 0)
            )
            bom.lines.append(line)
        
        bom.save()
        
        return jsonify(bom.to_dict()), 201
        
    except NotUniqueError:
        return _error_response(f"BOM for item {data['item_no']} version {data.get('version_code', 'V1')} already exists", 409)
    except ValidationError as e:
        return _validation_error(e)
    except Exception as e:
        return _error_response(f"Error creating BOM: {str(e)}", 500)

@bp.get("/<bom_id>")
@jwt_required()
def bom_get(bom_id: str):
    """Get a single BOM by ID"""
    lab = _get_lab()
    perm_err = _check_permission(lab, 'production', 'read')
    if perm_err:
        return perm_err
    
    try:
        bom = BOM.objects.get(id=bom_id, tenant_id=str(lab.id))
        return jsonify(bom.to_dict()), 200
    except DoesNotExist:
        return _not_found()

@bp.patch("/<bom_id>")
@jwt_required()
def bom_update(bom_id: str):
    """
    Update a BOM.
    
    Business Rules:
    - Can only update if status is New or Under Development
    - Cannot update Certified or Closed BOMs (must create new version)
    - Cannot change item_no or version_code (immutable)
    """
    lab = _get_lab()
    perm_err = _check_permission(lab, 'production', 'update')
    if perm_err:
        return perm_err
    
    try:
        bom = BOM.objects.get(id=bom_id, tenant_id=str(lab.id))
    except DoesNotExist:
        return _not_found()
    
    # Business rule: Cannot update Certified or Closed BOMs
    if bom.status in ["Certified", "Closed"]:
        return _error_response(f"Cannot update {bom.status} BOM. Create a new version instead.", 403)
    
    data = request.get_json()
    if not data:
        return _error_response("No data provided")
    
    user_email = get_jwt_identity()
    
    try:
        # Update allowed fields
        if "description" in data:
            bom.description = data["description"]
        if "status" in data and data["status"] in ["New", "Under Development"]:
            bom.status = data["status"]
        if "base_quantity" in data:
            bom.base_quantity = data["base_quantity"]
        if "base_uom" in data:
            bom.base_uom = data["base_uom"]
        if "is_phantom" in data:
            bom.is_phantom = data["is_phantom"]
        if "production_lead_time_days" in data:
            bom.production_lead_time_days = data["production_lead_time_days"]
        
        # Update lines if provided
        if "lines" in data:
            bom.lines = []
            for line_data in data["lines"]:
                # Verify component exists
                comp_item = Item.objects(tenant_id=str(lab.id), item_no=line_data["component_item_no"]).first()
                if not comp_item:
                    return _error_response(f"Component item {line_data['component_item_no']} not found", 404)
                
                line = BOMLine(
                    line_no=line_data["line_no"],
                    component_type=line_data.get("component_type", "Item"),
                    component_item_no=line_data["component_item_no"],
                    description=line_data.get("description", ""),
                    quantity_per=line_data["quantity_per"],
                    uom_code=line_data.get("uom_code"),
                    scrap_pct=line_data.get("scrap_pct", 0.0),
                    position=line_data.get("position"),
                    position_2=line_data.get("position_2"),
                    position_3=line_data.get("position_3"),
                    routing_link_code=line_data.get("routing_link_code"),
                    lead_time_offset=line_data.get("lead_time_offset", 0)
                )
                bom.lines.append(line)
        
        bom.updated_by = user_email
        bom.save()
        
        return jsonify(bom.to_dict()), 200
        
    except ValidationError as e:
        return _validation_error(e)
    except Exception as e:
        return _error_response(f"Error updating BOM: {str(e)}", 500)

@bp.delete("/<bom_id>")
@jwt_required()
def bom_delete(bom_id: str):
    """
    Delete a BOM.
    
    Business Rules:
    - Can only delete if status is New
    - Cannot delete Under Development, Certified, or Closed BOMs
    """
    lab = _get_lab()
    perm_err = _check_permission(lab, 'production', 'delete')
    if perm_err:
        return perm_err
    
    try:
        bom = BOM.objects.get(id=bom_id, tenant_id=str(lab.id))
    except DoesNotExist:
        return _not_found()
    
    # Business rule: Can only delete New BOMs
    if bom.status != "New":
        return _error_response(f"Cannot delete {bom.status} BOM. Only New BOMs can be deleted.", 403)
    
    # TODO: Check if BOM is used in Production Orders
    
    bom.delete()
    return jsonify({"message": "BOM deleted successfully"}), 200

@bp.post("/<bom_id>/certify")
@jwt_required()
def bom_certify(bom_id: str):
    """
    Certify a BOM (make it active).
    
    Business Rules:
    - Can only certify from Under Development status
    - Automatically uncertifies other versions of same item
    - Only one version can be Certified at a time
    """
    lab = _get_lab()
    perm_err = _check_permission(lab, 'production', 'update')
    if perm_err:
        return perm_err
    
    try:
        bom = BOM.objects.get(id=bom_id, tenant_id=str(lab.id))
    except DoesNotExist:
        return _not_found()
    
    # Business rule: Can only certify from Under Development
    if bom.status not in ["New", "Under Development"]:
        return _error_response(f"Cannot certify {bom.status} BOM. Must be New or Under Development.", 403)
    
    # Verify BOM has lines
    if not bom.lines:
        return _error_response("Cannot certify BOM with no lines", 400)
    
    user_email = get_jwt_identity()
    bom.certify(user_email)
    
    return jsonify(bom.to_dict()), 200

@bp.post("/<bom_id>/close")
@jwt_required()
def bom_close(bom_id: str):
    """
    Close a BOM (archive).
    
    Business Rules:
    - Can close any BOM except Closed
    - Typically used when a new version is certified
    """
    lab = _get_lab()
    perm_err = _check_permission(lab, 'production', 'update')
    if perm_err:
        return perm_err
    
    try:
        bom = BOM.objects.get(id=bom_id, tenant_id=str(lab.id))
    except DoesNotExist:
        return _not_found()
    
    if bom.status == "Closed":
        return _error_response("BOM is already closed", 400)
    
    user_email = get_jwt_identity()
    bom.close(user_email)
    
    return jsonify(bom.to_dict()), 200

@bp.get("/by-item/<item_no>")
@jwt_required()
def bom_by_item(item_no: str):
    """
    Get all BOM versions for a specific item.
    
    Returns BOMs ordered by version_code, with Certified first.
    """
    lab = _get_lab()
    perm_err = _check_permission(lab, 'production', 'read')
    if perm_err:
        return perm_err
    
    # Get all versions
    boms = BOM.objects(tenant_id=str(lab.id), item_no=item_no).order_by("-status", "version_code")
    
    return jsonify({
        "item_no": item_no,
        "total": boms.count(),
        "boms": [bom.to_dict() for bom in boms]
    }), 200

@bp.route('/certified/<item_no>', methods=['GET'])
@jwt_required()
def bom_certified(item_no: str):
    """Get the certified (active) BOM for an item"""
    lab = _get_lab()
    perm_err = _check_permission(lab, 'production', 'read')
    if perm_err:
        return perm_err
    
    bom = BOM.objects(tenant_id=str(lab.id), item_no=item_no, status="Certified").first()
    if not bom:
        return _error_response(f"No certified BOM found for item {item_no}", 404)
    
    return jsonify(bom.to_dict()), 200


@bp.route('/<bom_id>/explode', methods=['POST'])
@jwt_required()
def explode_bom_endpoint(bom_id: str):
    """
    Explode BOM to show all components (multi-level).
    
    Query Parameters:
        - quantity (float): Production quantity (default: 1.0)
        - check_availability (bool): Check inventory (default: false)
    
    Returns:
        - 200: Explosion result with hierarchy + consolidated components
        - 404: BOM not found
    
    Example:
        POST /api/production/boms/675a3b8f9d2e3a1b4c5d6e7f/explode?quantity=10
        {
            "item_no": "FG-CHAIR-001",
            "description": "Finished Chair",
            "quantity": 10,
            "status": "success",
            "components": [...],
            "consolidated_components": {...},
            "max_level": 2,
            "has_cycles": false
        }
    """
    lab = _get_lab()
    perm_err = _check_permission(lab, 'production', 'read')
    if perm_err:
        return perm_err
    
    # Get BOM
    try:
        bom = BOM.objects(id=bom_id, tenant_id=str(lab.id)).first()
        if not bom:
            return _not_found()
    except (DoesNotExist, ValidationError) as e:
        return _validation_error(e)
    
    # Validate status
    if bom.status not in ["Certified", "Under Development"]:
        return _error_response(
            f"Cannot explode BOM with status '{bom.status}'. Only Certified or Under Development BOMs can be exploded.",
            400
        )
    
    # Parse parameters
    try:
        quantity = float(request.args.get('quantity', 1.0))
        check_availability = request.args.get('check_availability', 'false').lower() == 'true'
    except ValueError:
        return _error_response("Invalid quantity parameter", 400)
    
    if quantity <= 0:
        return _error_response("Quantity must be positive", 400)
    
    # Perform explosion
    try:
        result = explode_bom(
            tenant_id=str(lab.id),
            item_no=bom.item_no,
            quantity=quantity,
            check_availability=check_availability
        )
        
        return jsonify(result.to_dict()), 200
    
    except Exception as e:
        return _error_response(f"Explosion failed: {str(e)}", 500)
