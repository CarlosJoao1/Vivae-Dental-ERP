# backend/routes/auth.py
from __future__ import annotations

from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_required,
)
from werkzeug.security import check_password_hash

# Ajusta o import do teu modelo de utilizador se necessário
from models.user import User  # <- confirmar caminho

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def _read_credentials():
    """
    Lê credenciais tanto de JSON como de form-data.
    Aceita 'username' ou 'email'.
    """
    data = request.get_json(silent=True) or {}
    if not data:
        # fallback para application/x-www-form-urlencoded ou multipart/form-data
        data = request.form.to_dict() if request.form else {}

    username = (data.get("username") or data.get("email") or "").strip()
    password = (data.get("password") or "").strip()
    return username, password


def _verify_password(user: User, plain: str) -> bool:
    """
    Tenta validar a password:
    1) via user.password_hash (hash com werkzeug)
    2) fallback: campo user.password em claro (apenas para compatibilidade)
    """
    if not user:
        return False

    # caminho habitual: hash em user.password_hash
    if hasattr(user, "password_hash") and getattr(user, "password_hash", None):
        try:
            return check_password_hash(user.password_hash, plain)
        except Exception:
            pass

    # fallback (não recomendado em produção, mas útil se seed tiver guardado em claro)
    if hasattr(user, "password") and getattr(user, "password", None):
        return str(user.password) == plain

    return False


def _user_public_payload(user: User) -> dict:
    """
    Normaliza o payload de utilizador devolvido ao frontend.
    Ajusta os nomes conforme o teu modelo (ex.: email, name, tenants, etc.)
    """
    return {
        "id": str(getattr(user, "id", "")),
        "username": getattr(user, "username", None),
        "email": getattr(user, "email", None),
        "roles": getattr(user, "roles", []) or [],
        "tenantId": (
            str(getattr(user, "tenant_id")) if getattr(user, "tenant_id", None) else None
        ),
        # "tenants": getattr(user, "tenants", []),  # ativa se tiveres esta relação
    }


def _extra_claims(user: User) -> dict:
    """
    Claims extra que colocamos no JWT (útil para RBAC/tenant no frontend).
    """
    claims = {
        "roles": getattr(user, "roles", []) or [],
        "tenantId": (
            str(getattr(user, "tenant_id")) if getattr(user, "tenant_id", None) else None
        ),
        "username": getattr(user, "username", None),
    }
    # Podes adicionar licensing/feature flags aqui, ex.:
    # claims["features"] = getattr(user, "features", [])
    return claims


@auth_bp.post("/login")
def login():
    username, password = _read_credentials()
    if not username or not password:
        return jsonify({"error": "missing credentials"}), 400

    # Tenta procurar por username e, se falhar, por email
    user = User.objects(username=username).first()
    if not user:
        user = User.objects(email=username).first()

    if not user or not _verify_password(user, password):
        return jsonify({"error": "invalid credentials"}), 401

    # JWTs
    identity = str(user.id)
    claims = _extra_claims(user)
    access_token = create_access_token(identity=identity, additional_claims=claims)
    refresh_token = create_refresh_token(identity=identity, additional_claims=claims)

    # payload para o frontend
    public_user = _user_public_payload(user)

    # Se tiveres tenants, podes incluí-los aqui
    tenants = []
    if hasattr(user, "tenants") and getattr(user, "tenants", None):
        try:
            tenants = [
                {"id": str(getattr(t, "id", "")) or str(getattr(t, "_id", "")), "name": getattr(t, "name", None)}
                for t in user.tenants
            ]
        except Exception:
            tenants = []

    return jsonify(
        {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": public_user,
            "tenants": tenants,
        }
    )


@auth_bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    """
    Recebe Authorization: Bearer <refresh_token>
    e devolve novo access (e opcionalmente refresh rotacionado).
    """
    user_id = get_jwt_identity()
    user = User.objects(id=user_id).first() if user_id else None
    if not user:
        return jsonify({"error": "invalid user"}), 401

    claims = _extra_claims(user)
    access_token = create_access_token(identity=str(user.id), additional_claims=claims)

    # Rotação de refresh é opcional. Se quiseres rotacionar:
    new_refresh = create_refresh_token(identity=str(user.id), additional_claims=claims)

    return jsonify({"access_token": access_token, "refresh_token": new_refresh})


@auth_bp.get("/me")
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = User.objects(id=user_id).first() if user_id else None
    if not user:
        return jsonify({"error": "not found"}), 404
    return jsonify({"user": _user_public_payload(user)})
