from flask import jsonify, g
from functools import wraps
from flask_jwt_extended import get_jwt_identity, get_jwt

from models.user import User
from services.permissions import ensure


def check_permission(lab, resource: str, action: str):
    """Common permission check used by production routes.

    - Sysadmin bypass via JWT claims
    - Load current user from JWT identity (id) with email fallback
    - Use services.permissions.ensure(user, lab, feature, action)
    Returns: None if allowed, or (json,error_code) tuple if denied.
    """
    try:
        claims = get_jwt() or {}
        if (claims.get('role') or '').lower() == 'sysadmin':
            return None
    except Exception:
        # If claims unavailable, proceed with regular path
        pass

    uid = get_jwt_identity()
    user = None
    try:
        user = User.objects.get(id=uid)
    except Exception:
        try:
            user = User.objects(email=uid).first()
        except Exception:
            user = None

    if not user:
        return jsonify({"error": "User not found"}), 401

    err = ensure(user, lab, resource, action)
    if err:
        return jsonify(err), 403
    return None


def require(action: str, feature: str = 'production', get_lab=None):
    """Decorator to enforce permission check before handler execution.

    Usage:
      @bp.get('/...')
      @jwt_required()
      @require('read', get_lab=_get_lab)
      def handler(): ...
    """
    def _decorator(fn):
        @wraps(fn)
        def _wrapped(*args, **kwargs):
            lab = get_lab() if callable(get_lab) else None
            try:
                g.lab = lab
            except Exception:
                pass
            resp = check_permission(lab, feature, action)
            if resp is not None:
                return resp
            return fn(*args, **kwargs)
        return _wrapped
    return _decorator
