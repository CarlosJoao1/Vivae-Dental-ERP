# backend/routes/tenants.py
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from models.laboratory import Laboratory

bp = Blueprint("tenants", __name__, url_prefix="/api")

@bp.get("/tenants")
@jwt_required()
def tenants_list():
    rows = Laboratory.objects.only("id","name").order_by("name")
    return jsonify({"tenants":[{"id": str(x.id), "name": x.name} for x in rows]})
