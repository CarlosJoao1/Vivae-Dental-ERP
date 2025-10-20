# backend/routes/production/work_centers.py
"""
Work Centers and Machine Centers Routes - NAV/BC-style
Endpoints for managing production resources (work centers and machines)
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from mongoengine.errors import ValidationError, DoesNotExist, NotUniqueError
from typing import Tuple

from models.production import WorkCenter, MachineCenter, Location
from models.laboratory import Laboratory
from models.user import User
from services.permissions import ensure

bp = Blueprint("production_work_centers", __name__, url_prefix="/api/production")

# ========================================
# HELPER FUNCTIONS (DRY pattern)
# ========================================

def _error_response(message: str, status: int = 400):
    """Standard error response"""
    return jsonify({"error": message}), status

def _not_found(resource: str = "Resource"):
    """Standard 404 response"""
    return jsonify({"error": f"{resource} not found"}), 404

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
# WORK CENTER ENDPOINTS
# ========================================

@bp.get("/work-centers")
@jwt_required()
def work_center_list():
    """
    List all Work Centers with filters and pagination.
    
    Query params:
    - page: Page number (default 1)
    - page_size: Items per page (default 50, max 100)
    - q: Search by code or name
    - blocked: Filter by blocked status (true/false)
    - location_code: Filter by location
    """
    lab = _get_lab()
    perm_err = _check_permission(lab, 'production', 'read')
    if perm_err:
        return perm_err
    
    page, size = _pagination()
    q = _query()
    
    # Base query
    qs = WorkCenter.objects(tenant_id=str(lab.id))
    
    # Search
    if q:
        qs = qs.filter(code__icontains=q) | WorkCenter.objects(tenant_id=str(lab.id), name__icontains=q)
    
    # Filters
    if request.args.get("blocked"):
        blocked = request.args["blocked"].lower() == "true"
        qs = qs.filter(blocked=blocked)
    
    if request.args.get("location_code"):
        qs = qs.filter(location_code=request.args["location_code"])
    
    # Pagination
    total = qs.count()
    items = qs.order_by("code").skip((page - 1) * size).limit(size)
    
    return jsonify({
        "total": total,
        "page": page,
        "page_size": size,
        "items": [wc.to_dict() for wc in items]
    }), 200

@bp.post("/work-centers")
@jwt_required()
def work_center_create():
    """
    Create a new Work Center.
    
    Body:
    {
        "code": "ASSEMBLY",
        "name": "Assembly Line 1",
        "description": "Main assembly line",
        "work_center_type": "Work Center",
        "capacity": 480.0,
        "efficiency_pct": 85.0,
        "unit_cost": 0.5,
        "location_code": "MAIN"
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
    if not data.get("code"):
        return _error_response("code is required")
    if not data.get("name"):
        return _error_response("name is required")
    
    # Verify location exists if provided
    if data.get("location_code"):
        location = Location.objects(tenant_id=str(lab.id), code=data["location_code"]).first()
        if not location:
            return _error_response(f"Location {data['location_code']} not found", 404)
    
    try:
        user_email = get_jwt_identity()
        
        wc = WorkCenter(
            tenant_id=str(lab.id),
            code=data["code"],
            name=data["name"],
            description=data.get("description", ""),
            work_center_type=data.get("work_center_type", "Work Center"),
            capacity=data.get("capacity", 480.0),
            efficiency_pct=data.get("efficiency_pct", 100.0),
            calendar_code=data.get("calendar_code"),
            unit_cost=data.get("unit_cost", 0.0),
            overhead_rate=data.get("overhead_rate", 0.0),
            location_code=data.get("location_code"),
            blocked=data.get("blocked", False),
            queue_time=data.get("queue_time", 0.0),
            created_by=user_email,
            updated_by=user_email
        )
        
        wc.save()
        
        return jsonify(wc.to_dict()), 201
        
    except NotUniqueError:
        return _error_response(f"Work Center with code {data['code']} already exists", 409)
    except ValidationError as e:
        return _validation_error(e)
    except Exception as e:
        return _error_response(f"Error creating Work Center: {str(e)}", 500)

@bp.get("/work-centers/<wc_id>")
@jwt_required()
def work_center_get(wc_id: str):
    """Get a single Work Center by ID"""
    lab = _get_lab()
    perm_err = _check_permission(lab, 'production', 'read')
    if perm_err:
        return perm_err
    
    try:
        wc = WorkCenter.objects.get(id=wc_id, tenant_id=str(lab.id))
        return jsonify(wc.to_dict()), 200
    except DoesNotExist:
        return _not_found("Work Center")

@bp.patch("/work-centers/<wc_id>")
@jwt_required()
def work_center_update(wc_id: str):
    """Update a Work Center"""
    lab = _get_lab()
    perm_err = _check_permission(lab, 'production', 'update')
    if perm_err:
        return perm_err
    
    try:
        wc = WorkCenter.objects.get(id=wc_id, tenant_id=str(lab.id))
    except DoesNotExist:
        return _not_found("Work Center")
    
    data = request.get_json()
    if not data:
        return _error_response("No data provided")
    
    user_email = get_jwt_identity()
    
    try:
        # Update allowed fields
        if "name" in data:
            wc.name = data["name"]
        if "description" in data:
            wc.description = data["description"]
        if "work_center_type" in data:
            wc.work_center_type = data["work_center_type"]
        if "capacity" in data:
            wc.capacity = data["capacity"]
        if "efficiency_pct" in data:
            wc.efficiency_pct = data["efficiency_pct"]
        if "calendar_code" in data:
            wc.calendar_code = data["calendar_code"]
        if "unit_cost" in data:
            wc.unit_cost = data["unit_cost"]
        if "overhead_rate" in data:
            wc.overhead_rate = data["overhead_rate"]
        if "location_code" in data:
            # Verify location exists if provided
            if data["location_code"]:
                location = Location.objects(tenant_id=str(lab.id), code=data["location_code"]).first()
                if not location:
                    return _error_response(f"Location {data['location_code']} not found", 404)
            wc.location_code = data["location_code"]
        if "blocked" in data:
            wc.blocked = data["blocked"]
        if "queue_time" in data:
            wc.queue_time = data["queue_time"]
        
        wc.updated_by = user_email
        wc.save()
        
        return jsonify(wc.to_dict()), 200
        
    except ValidationError as e:
        return _validation_error(e)
    except Exception as e:
        return _error_response(f"Error updating Work Center: {str(e)}", 500)

@bp.delete("/work-centers/<wc_id>")
@jwt_required()
def work_center_delete(wc_id: str):
    """
    Delete a Work Center.
    
    Business Rules:
    - Cannot delete if used in Routings
    - Cannot delete if has Machine Centers
    """
    lab = _get_lab()
    perm_err = _check_permission(lab, 'production', 'delete')
    if perm_err:
        return perm_err
    
    try:
        wc = WorkCenter.objects.get(id=wc_id, tenant_id=str(lab.id))
    except DoesNotExist:
        return _not_found("Work Center")
    
    # Check if has machine centers
    machine_count = MachineCenter.objects(tenant_id=str(lab.id), work_center_code=wc.code).count()
    if machine_count > 0:
        return _error_response(f"Cannot delete Work Center. It has {machine_count} Machine Center(s).", 403)
    
    # TODO: Check if used in Routings
    
    wc.delete()
    return jsonify({"message": "Work Center deleted successfully"}), 200

# ========================================
# MACHINE CENTER ENDPOINTS
# ========================================

@bp.get("/machine-centers")
@jwt_required()
def machine_center_list():
    """
    List all Machine Centers with filters and pagination.
    
    Query params:
    - page: Page number (default 1)
    - page_size: Items per page (default 50, max 100)
    - q: Search by code or name
    - work_center_code: Filter by parent work center
    - blocked: Filter by blocked status (true/false)
    """
    lab = _get_lab()
    perm_err = _check_permission(lab, 'production', 'read')
    if perm_err:
        return perm_err
    
    page, size = _pagination()
    q = _query()
    
    # Base query
    qs = MachineCenter.objects(tenant_id=str(lab.id))
    
    # Search
    if q:
        qs = qs.filter(code__icontains=q) | MachineCenter.objects(tenant_id=str(lab.id), name__icontains=q)
    
    # Filters
    if request.args.get("work_center_code"):
        qs = qs.filter(work_center_code=request.args["work_center_code"])
    
    if request.args.get("blocked"):
        blocked = request.args["blocked"].lower() == "true"
        qs = qs.filter(blocked=blocked)
    
    # Pagination
    total = qs.count()
    items = qs.order_by("code").skip((page - 1) * size).limit(size)
    
    return jsonify({
        "total": total,
        "page": page,
        "page_size": size,
        "items": [mc.to_dict() for mc in items]
    }), 200

@bp.post("/machine-centers")
@jwt_required()
def machine_center_create():
    """
    Create a new Machine Center.
    
    Body:
    {
        "code": "CNC-001",
        "name": "CNC Machine 1",
        "work_center_code": "MACHINING",
        "capacity": 480.0,
        "efficiency_pct": 90.0,
        "unit_cost": 1.5,
        "manufacturer": "HAAS",
        "model": "VF-2",
        "serial_number": "SN12345"
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
    if not data.get("code"):
        return _error_response("code is required")
    if not data.get("name"):
        return _error_response("name is required")
    if not data.get("work_center_code"):
        return _error_response("work_center_code is required")
    
    # Verify work center exists
    wc = WorkCenter.objects(tenant_id=str(lab.id), code=data["work_center_code"]).first()
    if not wc:
        return _error_response(f"Work Center {data['work_center_code']} not found", 404)
    
    try:
        user_email = get_jwt_identity()
        
        mc = MachineCenter(
            tenant_id=str(lab.id),
            code=data["code"],
            name=data["name"],
            description=data.get("description", ""),
            work_center_code=data["work_center_code"],
            capacity=data.get("capacity", 480.0),
            efficiency_pct=data.get("efficiency_pct", 100.0),
            calendar_code=data.get("calendar_code"),
            unit_cost=data.get("unit_cost", 0.0),
            overhead_rate=data.get("overhead_rate", 0.0),
            location_code=data.get("location_code"),
            blocked=data.get("blocked", False),
            queue_time=data.get("queue_time", 0.0),
            maintenance_interval_days=data.get("maintenance_interval_days"),
            manufacturer=data.get("manufacturer"),
            model=data.get("model"),
            serial_number=data.get("serial_number"),
            created_by=user_email,
            updated_by=user_email
        )
        
        mc.save()
        
        return jsonify(mc.to_dict()), 201
        
    except NotUniqueError:
        return _error_response(f"Machine Center with code {data['code']} already exists", 409)
    except ValidationError as e:
        return _validation_error(e)
    except Exception as e:
        return _error_response(f"Error creating Machine Center: {str(e)}", 500)

@bp.get("/machine-centers/<mc_id>")
@jwt_required()
def machine_center_get(mc_id: str):
    """Get a single Machine Center by ID"""
    lab = _get_lab()
    perm_err = _check_permission(lab, 'production', 'read')
    if perm_err:
        return perm_err
    
    try:
        mc = MachineCenter.objects.get(id=mc_id, tenant_id=str(lab.id))
        return jsonify(mc.to_dict()), 200
    except DoesNotExist:
        return _not_found("Machine Center")

@bp.patch("/machine-centers/<mc_id>")
@jwt_required()
def machine_center_update(mc_id: str):
    """Update a Machine Center"""
    lab = _get_lab()
    perm_err = _check_permission(lab, 'production', 'update')
    if perm_err:
        return perm_err
    
    try:
        mc = MachineCenter.objects.get(id=mc_id, tenant_id=str(lab.id))
    except DoesNotExist:
        return _not_found("Machine Center")
    
    data = request.get_json()
    if not data:
        return _error_response("No data provided")
    
    user_email = get_jwt_identity()
    
    try:
        # Update allowed fields
        if "name" in data:
            mc.name = data["name"]
        if "description" in data:
            mc.description = data["description"]
        if "work_center_code" in data:
            # Verify work center exists
            wc = WorkCenter.objects(tenant_id=str(lab.id), code=data["work_center_code"]).first()
            if not wc:
                return _error_response(f"Work Center {data['work_center_code']} not found", 404)
            mc.work_center_code = data["work_center_code"]
        if "capacity" in data:
            mc.capacity = data["capacity"]
        if "efficiency_pct" in data:
            mc.efficiency_pct = data["efficiency_pct"]
        if "calendar_code" in data:
            mc.calendar_code = data["calendar_code"]
        if "unit_cost" in data:
            mc.unit_cost = data["unit_cost"]
        if "overhead_rate" in data:
            mc.overhead_rate = data["overhead_rate"]
        if "location_code" in data:
            mc.location_code = data["location_code"]
        if "blocked" in data:
            mc.blocked = data["blocked"]
        if "queue_time" in data:
            mc.queue_time = data["queue_time"]
        if "maintenance_interval_days" in data:
            mc.maintenance_interval_days = data["maintenance_interval_days"]
        if "next_maintenance_date" in data:
            mc.next_maintenance_date = data["next_maintenance_date"]
        if "last_maintenance_date" in data:
            mc.last_maintenance_date = data["last_maintenance_date"]
        if "manufacturer" in data:
            mc.manufacturer = data["manufacturer"]
        if "model" in data:
            mc.model = data["model"]
        if "serial_number" in data:
            mc.serial_number = data["serial_number"]
        if "purchase_date" in data:
            mc.purchase_date = data["purchase_date"]
        
        mc.updated_by = user_email
        mc.save()
        
        return jsonify(mc.to_dict()), 200
        
    except ValidationError as e:
        return _validation_error(e)
    except Exception as e:
        return _error_response(f"Error updating Machine Center: {str(e)}", 500)

@bp.delete("/machine-centers/<mc_id>")
@jwt_required()
def machine_center_delete(mc_id: str):
    """
    Delete a Machine Center.
    
    Business Rules:
    - Cannot delete if used in Routing Operations
    """
    lab = _get_lab()
    perm_err = _check_permission(lab, 'production', 'delete')
    if perm_err:
        return perm_err
    
    try:
        mc = MachineCenter.objects.get(id=mc_id, tenant_id=str(lab.id))
    except DoesNotExist:
        return _not_found("Machine Center")
    
    # TODO: Check if used in Routing Operations
    
    mc.delete()
    return jsonify({"message": "Machine Center deleted successfully"}), 200

@bp.get("/work-centers/by-code/<code>")
@jwt_required()
def work_center_by_code(code: str):
    """Get a Work Center by code"""
    lab = _get_lab()
    perm_err = _check_permission(lab, 'production', 'read')
    if perm_err:
        return perm_err
    
    wc = WorkCenter.objects(tenant_id=str(lab.id), code=code).first()
    if not wc:
        return _not_found("Work Center")
    
    return jsonify(wc.to_dict()), 200

@bp.get("/machine-centers/by-work-center/<work_center_code>")
@jwt_required()
def machine_centers_by_work_center(work_center_code: str):
    """Get all Machine Centers for a Work Center"""
    lab = _get_lab()
    perm_err = _check_permission(lab, 'production', 'read')
    if perm_err:
        return perm_err
    
    machines = MachineCenter.objects(tenant_id=str(lab.id), work_center_code=work_center_code).order_by("code")
    
    return jsonify({
        "work_center_code": work_center_code,
        "total": machines.count(),
        "machines": [mc.to_dict() for mc in machines]
    }), 200
