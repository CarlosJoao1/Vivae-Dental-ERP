# backend/routes/health.py
from flask import Blueprint, jsonify
import os
from datetime import datetime, timezone
from typing import Any, Dict

try:
    from mongoengine.connection import get_db  # type: ignore
except Exception:  # pragma: no cover
    get_db = None  # type: ignore

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
    
    # Try to get branch name from git or env
    branch = os.getenv("RENDER_GIT_BRANCH") or os.getenv("GIT_BRANCH") or ""
    
    # If we have a branch, try to extract meaningful version from it
    if branch:
        # Remove common prefixes
        branch_clean = branch.replace("feature/", "").replace("hotfix/", "").replace("release/", "")
        
        # Check if branch looks like it has version info (contains digits)
        if any(c.isdigit() for c in branch_clean):
            # Try to extract something version-like
            parts = branch_clean.split("-")
            for part in parts:
                if any(c.isdigit() for c in part):
                    # Found a part with numbers, use it
                    return f"v{part}" if not part.startswith("v") else part
    
    # Fallback: v[AnoSemana].01 using ISO week
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

@bp.get("/api/health/deep")
def health_deep():
    """
    Deep health: checks backend is alive and DB connectivity (MongoDB ping).
    Returns fields helpful to diagnose Render/Atlas outages from the frontend.
    """
    data: Dict[str, Any] = {"ok": True}
    # Version/meta
    data["version"] = _compute_version()
    data["branch"] = os.getenv("RENDER_GIT_BRANCH") or os.getenv("GIT_BRANCH")
    data["commit"] = os.getenv("RENDER_GIT_COMMIT") or os.getenv("GIT_COMMIT")
    data["build_time"] = os.getenv("RENDER_BUILD_TIME")
    # Environment hints
    env_lower = (os.getenv("ENV", "") or os.getenv("FLASK_ENV", "")).lower()
    data["env"] = env_lower or None
    data["render"] = os.getenv("RENDER") == "true"
    data["has_secret_key"] = bool(os.getenv("SECRET_KEY"))
    data["has_jwt_secret_key"] = bool(os.getenv("JWT_SECRET_KEY"))
    data["has_mongo_uri"] = bool(os.getenv("MONGO_URI"))

    # DB ping
    db_status: Dict[str, Any] = {"ok": False}
    try:
        if get_db is None:
            raise RuntimeError("mongoengine not available")
        db = get_db(alias="default")  # type: ignore
        res = db.command("ping")
        db_status = {"ok": bool(res.get("ok")), "info": "pong"}
    except Exception as e:  # pragma: no cover
        db_status = {"ok": False, "error": str(e)}
        data["ok"] = False
    data["db"] = db_status
    return jsonify(data)
