from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from services.license_service import require_feature

bp = Blueprint("crm", __name__)

@bp.get("/status")
@jwt_required()
@require_feature("crm")
def crm_status():
    return jsonify({"feature":"crm","status":"ok"})
