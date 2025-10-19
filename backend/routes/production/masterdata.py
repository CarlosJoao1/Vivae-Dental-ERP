# backend/routes/production/masterdata.py
"""
Production Master Data Routes (NAV/BC-style)
Endpoints for UOM, Items, Locations, Suppliers
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from mongoengine.errors import ValidationError, DoesNotExist, NotUniqueError
from typing import Tuple

from models.production import UnitOfMeasure, Item, Location, Supplier
from models.laboratory import Laboratory
from models.user import User
from services.permissions import ensure

bp = Blueprint("production_masterdata", __name__, url_prefix="/api/production/masterdata")

# ========================================
# HELPER FUNCTIONS (DRY pattern)
# ========================================

def _error_response(message: str, status: int = 400):
    """Return JSON error response with status code"""
    return jsonify({"error": message}), status

def _not_found():
    """Return standard 404 not found response"""
    return _error_response("not found", 404)

def _validation_error(e: Exception):
    """Return validation error response"""
    return _error_response(str(e), 400)

def _check_permission(lab, resource: str, action: str):
    """Check user permission for resource action. Returns error response or None."""
    try:
        uid = get_jwt_identity()
        user = User.objects.get(id=uid)
        err = ensure(user, lab, resource, action)
        if err:
            return jsonify(err), 403
    except Exception:
        pass
    return None

def _get_lab() -> Laboratory:
    """Get laboratory from JWT or header"""
    from flask import current_app
    from flask_jwt_extended import get_jwt
    
    # Check for tenant override in header
    try:
        uid = get_jwt_identity()
    except Exception:
        uid = None
    
    header_tid = (request.headers.get("X-Tenant-Id") or "").strip()
    if uid and header_tid:
        try:
            user = User.objects.get(id=uid)
            if getattr(user, 'is_sysadmin', False):
                return Laboratory.objects.get(id=header_tid)
            allowed_ids = [str(getattr(x, 'id', '')) for x in (getattr(user, 'allowed_labs', []) or [])]
            if header_tid in allowed_ids:
                return Laboratory.objects.get(id=header_tid)
        except Exception:
            pass
    
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
# UNITS OF MEASURE (UOM)
# ========================================

@bp.get("/uom")
@jwt_required()
def uom_list():
    """List all Units of Measure"""
    lab = _get_lab()
    perm_err = _check_permission(lab, 'production', 'read')
    if perm_err:
        return perm_err
    
    page, size = _pagination()
    q = _query()
    
    qs = UnitOfMeasure.objects(tenant_id=lab)
    if q:
        qs = qs.filter(code__icontains=q) | UnitOfMeasure.objects(tenant_id=lab, description__icontains=q)
    
    total = qs.count()
    items = qs.order_by("code").skip((page - 1) * size).limit(size)
    
    return jsonify({
        "total": total,
        "page": page,
        "page_size": size,
        "items": [item.to_dict() for item in items]
    })

@bp.post("/uom")
@jwt_required()
def uom_create():
    """Create new Unit of Measure"""
    lab = _get_lab()
    perm_err = _check_permission(lab, 'production', 'create')
    if perm_err:
        return perm_err
    
    data = request.get_json(force=True, silent=True) or {}
    
    try:
        uid = get_jwt_identity()
        uom = UnitOfMeasure(
            tenant_id=lab,
            code=data.get("code"),
            description=data.get("description"),
            decimals=data.get("decimals", 0),
            created_by=uid,
            updated_by=uid,
        ).save()
        
        return jsonify({"uom": uom.to_dict()}), 201
    except NotUniqueError:
        return _error_response(f"UOM code '{data.get('code')}' already exists", 409)
    except (ValidationError, Exception) as e:
        return _validation_error(e)

@bp.patch("/uom/<uom_id>")
@jwt_required()
def uom_update(uom_id):
    """Update Unit of Measure"""
    lab = _get_lab()
    perm_err = _check_permission(lab, 'production', 'update')
    if perm_err:
        return perm_err
    
    data = request.get_json(force=True, silent=True) or {}
    
    try:
        uid = get_jwt_identity()
        uom = UnitOfMeasure.objects.get(id=uom_id, tenant_id=lab)
        
        # Update fields
        if "description" in data:
            uom.description = data["description"]
        if "decimals" in data:
            uom.decimals = data["decimals"]
        
        uom.updated_by = uid
        uom.save()
        
        return jsonify({"uom": uom.to_dict()})
    except DoesNotExist:
        return _not_found()
    except (ValidationError, Exception) as e:
        return _validation_error(e)

@bp.delete("/uom/<uom_id>")
@jwt_required()
def uom_delete(uom_id):
    """Delete Unit of Measure"""
    lab = _get_lab()
    perm_err = _check_permission(lab, 'production', 'delete')
    if perm_err:
        return perm_err
    
    try:
        uom = UnitOfMeasure.objects.get(id=uom_id, tenant_id=lab)
        
        # Check if UOM is used by items
        item_count = Item.objects(tenant_id=lab, base_uom=uom.code).count()
        if item_count > 0:
            return _error_response(f"Cannot delete UOM '{uom.code}': used by {item_count} item(s)", 409)
        
        uom.delete()
        return jsonify({"status": "deleted"})
    except DoesNotExist:
        return _not_found()

# ========================================
# ITEMS
# ========================================

@bp.get("/items")
@jwt_required()
def items_list():
    """List all Items"""
    lab = _get_lab()
    perm_err = _check_permission(lab, 'production', 'read')
    if perm_err:
        return perm_err
    
    page, size = _pagination()
    q = _query()
    item_type = request.args.get("item_type")  # Filter by type
    status = request.args.get("status")  # Filter by status
    
    qs = Item.objects(tenant_id=lab)
    
    if q:
        qs = qs.filter(item_no__icontains=q) | Item.objects(tenant_id=lab, description__icontains=q)
    if item_type:
        qs = qs.filter(item_type=item_type)
    if status:
        qs = qs.filter(status=status)
    
    total = qs.count()
    items = qs.order_by("item_no").skip((page - 1) * size).limit(size)
    
    return jsonify({
        "total": total,
        "page": page,
        "page_size": size,
        "items": [item.to_dict() for item in items]
    })

@bp.post("/items")
@jwt_required()
def items_create():
    """Create new Item"""
    lab = _get_lab()
    perm_err = _check_permission(lab, 'production', 'create')
    if perm_err:
        return perm_err
    
    data = request.get_json(force=True, silent=True) or {}
    
    try:
        uid = get_jwt_identity()
        
        # Validate UOM exists
        uom_code = data.get("base_uom")
        if not UnitOfMeasure.objects(tenant_id=lab, code=uom_code).first():
            return _error_response(f"UOM '{uom_code}' does not exist", 400)
        
        item = Item(
            tenant_id=lab,
            item_no=data.get("item_no"),
            description=data.get("description"),
            description_2=data.get("description_2"),
            item_type=data.get("item_type", "manufactured"),
            base_uom=uom_code,
            default_supplier_id=data.get("default_supplier_id"),
            lead_time_days=data.get("lead_time_days", 0),
            safety_stock_qty=data.get("safety_stock_qty", 0),
            reorder_point=data.get("reorder_point"),
            reorder_quantity=data.get("reorder_quantity"),
            unit_cost=data.get("unit_cost"),
            costing_method=data.get("costing_method", "standard"),
            status=data.get("status", "Active"),
            critical_item=data.get("critical_item", False),
            phantom_bom=data.get("phantom_bom", False),
            created_by=uid,
            updated_by=uid,
        ).save()
        
        return jsonify({"item": item.to_dict()}), 201
    except NotUniqueError:
        return _error_response(f"Item '{data.get('item_no')}' already exists", 409)
    except (ValidationError, Exception) as e:
        return _validation_error(e)

@bp.patch("/items/<item_id>")
@jwt_required()
def items_update(item_id):
    """Update Item"""
    lab = _get_lab()
    perm_err = _check_permission(lab, 'production', 'update')
    if perm_err:
        return perm_err
    
    data = request.get_json(force=True, silent=True) or {}
    
    try:
        uid = get_jwt_identity()
        item = Item.objects.get(id=item_id, tenant_id=lab)
        
        # Update fields
        updateable_fields = [
            'description', 'description_2', 'item_type', 'base_uom', 
            'default_supplier_id', 'lead_time_days', 'safety_stock_qty',
            'reorder_point', 'reorder_quantity', 'unit_cost', 
            'costing_method', 'status', 'critical_item', 'phantom_bom'
        ]
        
        for field in updateable_fields:
            if field in data:
                setattr(item, field, data[field])
        
        item.updated_by = uid
        item.save()
        
        return jsonify({"item": item.to_dict()})
    except DoesNotExist:
        return _not_found()
    except (ValidationError, Exception) as e:
        return _validation_error(e)

@bp.delete("/items/<item_id>")
@jwt_required()
def items_delete(item_id):
    """Delete Item"""
    lab = _get_lab()
    perm_err = _check_permission(lab, 'production', 'delete')
    if perm_err:
        return perm_err
    
    try:
        item = Item.objects.get(id=item_id, tenant_id=lab)
        
        # TODO: Check if item is used in BOMs, orders, etc.
        # For now, allow deletion
        
        item.delete()
        return jsonify({"status": "deleted"})
    except DoesNotExist:
        return _not_found()

# ========================================
# LOCATIONS
# ========================================

@bp.get("/locations")
@jwt_required()
def locations_list():
    """List all Locations"""
    lab = _get_lab()
    perm_err = _check_permission(lab, 'production', 'read')
    if perm_err:
        return perm_err
    
    page, size = _pagination()
    q = _query()
    
    qs = Location.objects(tenant_id=lab)
    if q:
        qs = qs.filter(code__icontains=q) | Location.objects(tenant_id=lab, name__icontains=q)
    
    total = qs.count()
    items = qs.order_by("code").skip((page - 1) * size).limit(size)
    
    return jsonify({
        "total": total,
        "page": page,
        "page_size": size,
        "items": [item.to_dict() for item in items]
    })

@bp.post("/locations")
@jwt_required()
def locations_create():
    """Create new Location"""
    lab = _get_lab()
    perm_err = _check_permission(lab, 'production', 'create')
    if perm_err:
        return perm_err
    
    data = request.get_json(force=True, silent=True) or {}
    
    try:
        uid = get_jwt_identity()
        
        location = Location(
            tenant_id=lab,
            code=data.get("code"),
            name=data.get("name"),
            address=data.get("address"),
            address_2=data.get("address_2"),
            city=data.get("city"),
            postal_code=data.get("postal_code"),
            country_code=data.get("country_code"),
            contact_name=data.get("contact_name"),
            phone_no=data.get("phone_no"),
            email=data.get("email"),
            allow_negative_stock=data.get("allow_negative_stock", False),
            require_pick=data.get("require_pick", False),
            require_put_away=data.get("require_put_away", False),
            is_default=data.get("is_default", False),
            blocked=data.get("blocked", False),
            created_by=uid,
            updated_by=uid,
        ).save()
        
        return jsonify({"location": location.to_dict()}), 201
    except NotUniqueError:
        return _error_response(f"Location '{data.get('code')}' already exists", 409)
    except (ValidationError, Exception) as e:
        return _validation_error(e)

@bp.patch("/locations/<location_id>")
@jwt_required()
def locations_update(location_id):
    """Update Location"""
    lab = _get_lab()
    perm_err = _check_permission(lab, 'production', 'update')
    if perm_err:
        return perm_err
    
    data = request.get_json(force=True, silent=True) or {}
    
    try:
        uid = get_jwt_identity()
        location = Location.objects.get(id=location_id, tenant_id=lab)
        
        # Update fields
        updateable_fields = [
            'name', 'address', 'address_2', 'city', 'postal_code', 'country_code',
            'contact_name', 'phone_no', 'email', 'allow_negative_stock',
            'require_pick', 'require_put_away', 'is_default', 'blocked'
        ]
        
        for field in updateable_fields:
            if field in data:
                setattr(location, field, data[field])
        
        location.updated_by = uid
        location.save()
        
        return jsonify({"location": location.to_dict()})
    except DoesNotExist:
        return _not_found()
    except (ValidationError, Exception) as e:
        return _validation_error(e)

@bp.delete("/locations/<location_id>")
@jwt_required()
def locations_delete(location_id):
    """Delete Location"""
    lab = _get_lab()
    perm_err = _check_permission(lab, 'production', 'delete')
    if perm_err:
        return perm_err
    
    try:
        location = Location.objects.get(id=location_id, tenant_id=lab)
        
        # TODO: Check if location is used in inventory, orders, etc.
        # For now, allow deletion
        
        location.delete()
        return jsonify({"status": "deleted"})
    except DoesNotExist:
        return _not_found()

# ========================================
# SUPPLIERS
# ========================================

@bp.get("/suppliers")
@jwt_required()
def suppliers_list():
    """List all Suppliers"""
    lab = _get_lab()
    perm_err = _check_permission(lab, 'production', 'read')
    if perm_err:
        return perm_err
    
    page, size = _pagination()
    q = _query()
    status = request.args.get("status")
    
    qs = Supplier.objects(tenant_id=lab)
    
    if q:
        qs = qs.filter(supplier_id__icontains=q) | Supplier.objects(tenant_id=lab, name__icontains=q)
    if status:
        qs = qs.filter(status=status)
    
    total = qs.count()
    items = qs.order_by("supplier_id").skip((page - 1) * size).limit(size)
    
    return jsonify({
        "total": total,
        "page": page,
        "page_size": size,
        "items": [item.to_dict() for item in items]
    })

@bp.post("/suppliers")
@jwt_required()
def suppliers_create():
    """Create new Supplier"""
    lab = _get_lab()
    perm_err = _check_permission(lab, 'production', 'create')
    if perm_err:
        return perm_err
    
    data = request.get_json(force=True, silent=True) or {}
    
    try:
        uid = get_jwt_identity()
        
        supplier = Supplier(
            tenant_id=lab,
            supplier_id=data.get("supplier_id"),
            name=data.get("name"),
            name_2=data.get("name_2"),
            address=data.get("address"),
            address_2=data.get("address_2"),
            city=data.get("city"),
            postal_code=data.get("postal_code"),
            country_code=data.get("country_code"),
            phone_no=data.get("phone_no"),
            mobile_no=data.get("mobile_no"),
            email=data.get("email"),
            home_page=data.get("home_page"),
            contacts=data.get("contacts", []),
            lead_time_days_default=data.get("lead_time_days_default", 0),
            currency_code=data.get("currency_code", "EUR"),
            payment_terms_code=data.get("payment_terms_code"),
            payment_method_code=data.get("payment_method_code"),
            preferred_items=data.get("preferred_items", []),
            rating=data.get("rating"),
            supplier_class=data.get("supplier_class"),
            vat_registration_no=data.get("vat_registration_no"),
            tax_id=data.get("tax_id"),
            credit_limit=data.get("credit_limit"),
            status=data.get("status", "Active"),
            preferred_supplier=data.get("preferred_supplier", False),
            created_by=uid,
            updated_by=uid,
        ).save()
        
        return jsonify({"supplier": supplier.to_dict()}), 201
    except NotUniqueError:
        return _error_response(f"Supplier '{data.get('supplier_id')}' already exists", 409)
    except (ValidationError, Exception) as e:
        return _validation_error(e)

@bp.patch("/suppliers/<supplier_id>")
@jwt_required()
def suppliers_update(supplier_id):
    """Update Supplier"""
    lab = _get_lab()
    perm_err = _check_permission(lab, 'production', 'update')
    if perm_err:
        return perm_err
    
    data = request.get_json(force=True, silent=True) or {}
    
    try:
        uid = get_jwt_identity()
        supplier = Supplier.objects.get(id=supplier_id, tenant_id=lab)
        
        # Update fields
        updateable_fields = [
            'name', 'name_2', 'address', 'address_2', 'city', 'postal_code', 'country_code',
            'phone_no', 'mobile_no', 'email', 'home_page', 'contacts',
            'lead_time_days_default', 'currency_code', 'payment_terms_code', 
            'payment_method_code', 'preferred_items', 'rating', 'supplier_class',
            'vat_registration_no', 'tax_id', 'credit_limit', 'status', 
            'blocked_reason', 'preferred_supplier'
        ]
        
        for field in updateable_fields:
            if field in data:
                setattr(supplier, field, data[field])
        
        supplier.updated_by = uid
        supplier.save()
        
        return jsonify({"supplier": supplier.to_dict()})
    except DoesNotExist:
        return _not_found()
    except (ValidationError, Exception) as e:
        return _validation_error(e)

@bp.delete("/suppliers/<supplier_id>")
@jwt_required()
def suppliers_delete(supplier_id):
    """Delete Supplier"""
    lab = _get_lab()
    perm_err = _check_permission(lab, 'production', 'delete')
    if perm_err:
        return perm_err
    
    try:
        supplier = Supplier.objects.get(id=supplier_id, tenant_id=lab)
        
        # Check if supplier is default for any items
        item_count = Item.objects(tenant_id=lab, default_supplier_id=supplier.supplier_id).count()
        if item_count > 0:
            return _error_response(
                f"Cannot delete supplier '{supplier.supplier_id}': set as default for {item_count} item(s)", 
                409
            )
        
        supplier.delete()
        return jsonify({"status": "deleted"})
    except DoesNotExist:
        return _not_found()
