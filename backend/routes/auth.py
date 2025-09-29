# backend/routes/auth.py
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    jwt_required, create_access_token, create_refresh_token, get_jwt_identity
)
from models.user import User
from mongoengine.errors import DoesNotExist
import json

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def _parse_credentials():
    """
    Extrai username/password de:
      1) JSON (application/json)
      2) Form (application/x-www-form-urlencoded ou multipart)
      3) request.data (fallback bruto)
      4) Querystring (último recurso)
    """
    data = request.get_json(silent=True) or {}

    if not data and request.form:
        data = request.form.to_dict()

    if not data and request.data:
        try:
            data = json.loads(request.data.decode("utf-8"))
        except Exception:
            data = {}

    username = (data.get("username") or request.args.get("username") or "").strip()
    password = data.get("password") or request.args.get("password") or ""

    # Log leve p/ diagnosticar payload inesperado (sem password)
    if not username or not password:
        try:
            preview = {k: ("***" if k.lower() == "password" else v) for k, v in dict(data).items()}
            current_app.logger.warning(
                "Login payload vazio/inesperado. CT=%s, data=%s",
                request.headers.get("Content-Type"), preview
            )
        except Exception:
            pass

    return username, password


# (Opcional) Responder explicitamente ao preflight, sem usar @bp.options
@bp.route("/login", methods=["OPTIONS"])
def login_options():
    return ("", 204)


@bp.post("/login")
def login():
    username, password = _parse_credentials()
    if not username or not password:
        return jsonify({"error": "missing credentials"}), 400

    try:
        user = User.objects.get(username=username)
    except DoesNotExist:
        return jsonify({"error": "invalid credentials"}), 401

    if not user.check_password(password):
        return jsonify({"error": "invalid credentials"}), 401

    claims = {
        "role": getattr(user, "role", None),
        "tenant_id": str(getattr(user, "tenant_id", None)) if getattr(user, "tenant_id", None) else None
    }
    access = create_access_token(identity=str(user.id), additional_claims=claims)
    refresh = create_refresh_token(identity=str(user.id), additional_claims=claims)
    return jsonify({"access_token": access, "refresh_token": refresh})


@bp.route("/refresh", methods=["OPTIONS"])
def refresh_options():
    return ("", 204)


@bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    user_id = get_jwt_identity()
    user = User.objects.get(id=user_id)
    claims = {
        "role": getattr(user, "role", None),
        "tenant_id": str(getattr(user, "tenant_id", None)) if getattr(user, "tenant_id", None) else None
    }
    access = create_access_token(identity=str(user.id), additional_claims=claims)
    return jsonify({"access_token": access})


@bp.route("/me", methods=["OPTIONS"])
def me_options():
    return ("", 204)


@bp.get("/me")
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = User.objects.get(id=user_id)
    return jsonify({
        "id": str(user.id),
        "username": user.username,
        "email": getattr(user, "email", None),
        "role": getattr(user, "role", None),
        "tenant_id": str(getattr(user, "tenant_id", None)) if getattr(user, "tenant_id", None) else None
    })


@bp.post("/register")
def register():
    data = request.get_json(force=True, silent=True) or request.form.to_dict() or {}
    if not data.get("username") or not data.get("password"):
        return jsonify({"error": "username & password required"}), 400
    if User.objects(username=data["username"]).first():
        return jsonify({"error": "username exists"}), 409
    u = User(
        username=data["username"],
        email=data.get("email"),
        role=data.get("role", "user"),
    )
    u.set_password(data["password"])
    u.save()
    return jsonify({"id": str(u.id), "username": u.username}), 201
