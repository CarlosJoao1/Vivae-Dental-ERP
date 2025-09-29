# backend/routes/auth.py
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    jwt_required, create_access_token, create_refresh_token, get_jwt_identity
)
from models.user import User
from mongoengine.errors import DoesNotExist
import json, base64

bp = Blueprint("auth", __name__, url_prefix="/api/auth")

def _parse_json_body() -> dict:
    """
    Tenta obter JSON do body de forma robusta. Se falhar, tenta fazer
    loads do raw body. Devolve {} se nada útil for encontrado.
    """
    data = request.get_json(silent=True)
    if isinstance(data, dict) and data:
        return data
    raw = request.get_data(cache=False, as_text=True)
    if raw:
        try:
            obj = json.loads(raw)
            if isinstance(obj, dict):
                return obj
        except Exception:
            pass
    return {}

def _basic_auth_creds() -> dict:
    """Lê credenciais de Authorization: Basic ... (apenas para debug/testes)."""
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Basic "):
        try:
            decoded = base64.b64decode(auth.split(" ", 1)[1]).decode("utf-8")
            user, pwd = decoded.split(":", 1)
            return {"username": user, "password": pwd}
        except Exception:
            pass
    return {}

def _get_credentials():
    """
    Extrai username/password por esta ordem:
    - JSON body
    - form/multipart (request.form)
    - Basic Auth (Authorization: Basic ...)
    """
    data = _parse_json_body()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        f = request.form or {}
        username = username or f.get("username")
        password = password or f.get("password")

    if not username or not password:
        ba = _basic_auth_creds()
        username = username or ba.get("username")
        password = password or ba.get("password")

    return username, password

@bp.post("/login")
def login():
    username, password = _get_credentials()
    if not username or not password:
        # Log útil para diagnosticar em produção
        ct = request.headers.get("Content-Type")
        try:
            raw_len = len(request.get_data(cache=False) or b"")
        except Exception:
            raw_len = -1
        current_app.logger.warning(
            "Login payload vazio/inesperado. CT=%s raw_len=%s form_keys=%s",
            ct, raw_len, list(request.form.keys())
        )
        return jsonify({"error": "missing credentials"}), 400

    try:
        user = User.objects.get(username=username)
    except DoesNotExist:
        return jsonify({"error": "invalid credentials"}), 401

    if not user.check_password(password):
        return jsonify({"error": "invalid credentials"}), 401

    claims = {
        "role": user.role,
        "tenant_id": str(user.tenant_id) if getattr(user, "tenant_id", None) else None
    }
    access = create_access_token(identity=str(user.id), additional_claims=claims)
    refresh = create_refresh_token(identity=str(user.id), additional_claims=claims)
    return jsonify({"access_token": access, "refresh_token": refresh})

@bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    user_id = get_jwt_identity()
    user = User.objects.get(id=user_id)
    claims = {
        "role": user.role,
        "tenant_id": str(user.tenant_id) if getattr(user, "tenant_id", None) else None
    }
    access = create_access_token(identity=str(user.id), additional_claims=claims)
    return jsonify({"access_token": access})

@bp.get("/me")
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = User.objects.get(id=user_id)
    return jsonify({
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "tenant_id": str(user.tenant_id) if getattr(user, "tenant_id", None) else None
    })

@bp.post("/register")
def register():
    data = _parse_json_body()
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return jsonify({"error": "username & password required"}), 400
    if User.objects(username=username).first():
        return jsonify({"error": "username exists"}), 409
    u = User(
        username=username,
        email=data.get("email"),
        role=data.get("role", "user"),
    )
    u.set_password(password)
    u.save()
    return jsonify({"id": str(u.id), "username": u.username}), 201
