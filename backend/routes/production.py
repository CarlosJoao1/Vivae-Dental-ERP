from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from services.license_service import require_feature

bp = Blueprint("production", __name__)

@bp.get("/status")
@jwt_required()
@require_feature("producao")
def prod_status():
    return jsonify({"feature": "producao", "status": "ok"})
