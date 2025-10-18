from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.user import User
from models.laboratory import Laboratory
from models.role_policy import RolePolicy

bp = Blueprint("roles", __name__, url_prefix="/api/roles")


FEATURES = [
    {"key": "clients", "label": "Clients", "actions": ["read", "create", "update", "delete"]},
    {"key": "patients", "label": "Patients", "actions": ["read", "create", "update", "delete"]},
    {"key": "technicians", "label": "Technicians", "actions": ["read", "create", "update", "delete"]},
    {"key": "services", "label": "Services", "actions": ["read", "create", "update", "delete"]},
    {"key": "document_types", "label": "Document Types", "actions": ["read", "create", "update", "delete"]},
    {"key": "countries", "label": "Countries", "actions": ["read", "create", "update", "delete"]},
    {"key": "shipping_addresses", "label": "Shipping Addresses", "actions": ["read", "create", "update", "delete"]},
    {"key": "client_prices", "label": "Client Prices", "actions": ["read", "create", "update", "delete"]},
    {"key": "sales_orders", "label": "Sales Orders", "actions": ["read", "create", "update", "delete"]},
    {"key": "sales_invoices", "label": "Sales Invoices", "actions": ["read", "create", "update", "delete"]},
    {"key": "smtp", "label": "SMTP Settings", "actions": ["read", "update"]},
    {"key": "series", "label": "Series", "actions": ["read", "create", "update"]},
    {"key": "users", "label": "Users", "actions": ["read", "create", "update"]},
    {"key": "laboratories", "label": "Laboratories", "actions": ["read", "create", "update"]},
]


def _get_current_user() -> User:
    uid = get_jwt_identity()
    return User.objects.get(id=uid)


def _lab_from_header_or_user(user: User) -> Laboratory | None:
    tid = (request.headers.get("X-Tenant-Id") or "").strip()
    if tid:
        try:
            if getattr(user, "is_sysadmin", False):
                return Laboratory.objects.get(id=tid)
            # non-sysadmin: only if tenant in allowed_labs
            allowed_ids = [str(getattr(x, 'id', '')) for x in (getattr(user, 'allowed_labs', []) or [])]
            if tid in allowed_ids:
                return Laboratory.objects.get(id=tid)
            return None
        except Exception:
            return None
    return getattr(user, "tenant_id", None)


@bp.get("/features")
@jwt_required()
def list_features():
    return jsonify({"items": FEATURES})


@bp.get("/policies")
@jwt_required()
def get_policies():
    user = _get_current_user()
    lab = _lab_from_header_or_user(user)
    if not lab:
        return jsonify({"error": "tenant required"}), 400
    # Only sysadmin or lab admin can read policies
    if not getattr(user, "is_sysadmin", False) and (user.role or "").lower() != "admin":
        return jsonify({"error": "not allowed"}), 403
    rp = RolePolicy.objects(lab=lab).first()
    return jsonify({"lab_id": str(getattr(lab, 'id', '')), "policies": (rp.policies if rp else {})})


@bp.put("/policies")
@jwt_required()
def update_policies():
    user = _get_current_user()
    lab = _lab_from_header_or_user(user)
    if not lab:
        return jsonify({"error": "tenant required"}), 400
    # Only sysadmin or lab admin can update policies
    if not getattr(user, "is_sysadmin", False) and (user.role or "").lower() != "admin":
        return jsonify({"error": "not allowed"}), 403
    data = request.get_json(force=True, silent=True) or {}
    policies = data.get("policies") or {}
    if not isinstance(policies, dict):
        return jsonify({"error": "policies must be dict"}), 400
    rp = RolePolicy.objects(lab=lab).first() or RolePolicy(lab=lab)
    rp.policies = policies
    rp.save()
    return jsonify({"ok": True})

