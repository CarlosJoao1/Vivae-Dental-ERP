# backend/routes/masterdata.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from mongoengine.errors import ValidationError, DoesNotExist

from models.laboratory import Laboratory

bp = Blueprint("masterdata", __name__, url_prefix="/api/masterdata")

def _lab_to_dict(l: Laboratory):
    return {
        "id": str(l.id),
        "name": l.name,
        "address": l.address or "",
        "country": l.country or "",
        "postal_code": l.postal_code or "",
        "city": l.city or "",
        "tax_id": l.tax_id or "",
        "phone": l.phone or "",
        "email": l.email or "",
        "active": bool(getattr(l, "active", True)),
    }

# Laboratories
@bp.get("/laboratories")
@jwt_required()
def labs_list():
    labs = Laboratory.objects.order_by("name")
    return jsonify({"laboratories": [_lab_to_dict(x) for x in labs]})

@bp.post("/laboratories")
@jwt_required()
def labs_create():
    data = request.get_json(force=True, silent=True) or {}
    try:
        lab = Laboratory(
            name=data.get("name"),
            address=data.get("address"),
            country=data.get("country"),
            postal_code=data.get("postal_code"),
            city=data.get("city"),
            tax_id=data.get("tax_id"),
            phone=data.get("phone"),
            email=data.get("email"),
            active=data.get("active", True),
        ).save()
        return jsonify({"laboratory": _lab_to_dict(lab)}), 201
    except (ValidationError, Exception) as e:
        return jsonify({"error": str(e)}), 400

@bp.put("/laboratories/<lab_id>")
@jwt_required()
def labs_update(lab_id):
    data = request.get_json(force=True, silent=True) or {}
    try:
        lab = Laboratory.objects.get(id=lab_id)
        for f in ["name","address","country","postal_code","city","tax_id","phone","email","active"]:
            if f in data: setattr(lab, f, data[f])
        lab.save()
        return jsonify({"laboratory": _lab_to_dict(lab)})
    except DoesNotExist:
        return jsonify({"error": "not found"}), 404
    except (ValidationError, Exception) as e:
        return jsonify({"error": str(e)}), 400

# Stubs for other masterdata entities (patients, technicians, services, doctypes)
@bp.get("/patients")
@jwt_required()
def patients_list():
    return jsonify({"patients": []})

@bp.post("/patients")
@jwt_required()
def patients_create():
    return jsonify({"status":"created"}), 201

@bp.get("/technicians")
@jwt_required()
def techs_list():
    return jsonify({"technicians": []})

@bp.post("/technicians")
@jwt_required()
def techs_create():
    return jsonify({"status":"created"}), 201

@bp.get("/services")
@jwt_required()
def services_list():
    return jsonify({"services": []})

@bp.post("/services")
@jwt_required()
def services_create():
    return jsonify({"status":"created"}), 201

@bp.get("/document-types")
@jwt_required()
def doctypes_list():
    return jsonify({"document_types": []})

@bp.post("/document-types")
@jwt_required()
def doctypes_create():
    return jsonify({"status":"created"}), 201
