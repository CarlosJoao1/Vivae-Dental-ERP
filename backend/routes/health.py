# backend/routes/health.py
from flask import Blueprint, jsonify

bp = Blueprint("health", __name__)

@bp.get("/")
def root():
    return "Vivae Dental ERP backend online", 200

@bp.get("/api")
def api_root():
    return jsonify({
        "status": "ok",
        "name": "Vivae Dental ERP API",
        "version": "0.1.0",
        "endpoints_hint": [
            "/api/auth/login",
            "/api/auth/refresh",
            "/api/auth/me",
            "/api/tenants",
            "/api/masterdata/laboratories",
            "/api/masterdata/patients",
            "/api/masterdata/technicians",
            "/api/masterdata/services",
            "/api/masterdata/document-types",
            "/api/health"
        ]
    })

@bp.get("/api/health")
def health():
    return jsonify({"ok": True})
