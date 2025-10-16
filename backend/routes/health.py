# backend/routes/health.py
from flask import Blueprint, jsonify
import os
from datetime import datetime, timezone

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

def _iso_year_week(dt: datetime) -> str:
    y, w, _ = dt.isocalendar()
    return f"{y}{w:02d}"

def _compute_version() -> str:
    # Prefer APP_VERSION from env if set
    ev = (os.getenv("APP_VERSION") or "").strip()
    if ev:
        return ev
    # Default: v[AnoSemana].01 using ISO week
    # Use timezone-aware UTC datetime
    base = _iso_year_week(datetime.now(timezone.utc))
    return f"v{base}.01"

@bp.get("/api/health/info")
def health_info():
    version = _compute_version()
    # Render provides these on build/runtime; if absent, keep None
    branch = os.getenv("RENDER_GIT_BRANCH") or os.getenv("GIT_BRANCH")
    commit = os.getenv("RENDER_GIT_COMMIT") or os.getenv("GIT_COMMIT")
    build_time = os.getenv("RENDER_BUILD_TIME")
    return jsonify({
        "ok": True,
        "version": version,
        "branch": branch,
        "commit": commit,
        "build_time": build_time,
    })
