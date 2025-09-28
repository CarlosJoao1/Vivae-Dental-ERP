# backend/routes/auth.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    jwt_required, create_access_token, create_refresh_token,
    get_jwt_identity
)
from models.user import User
from mongoengine.errors import DoesNotExist

bp = Blueprint("auth", __name__, url_prefix="/api/auth")

@bp.post("/login")
def login():
    data = request.get_json(force=True, silent=True) or {}
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return jsonify({"error": "missing credentials"}), 400
    try:
        user = User.objects.get(username=username)
    except DoesNotExist:
        return jsonify({"error": "invalid credentials"}), 401
    if not user.check_password(password):
        return jsonify({"error": "invalid credentials"}), 401
    claims = {"role": user.role, "tenant_id": str(user.tenant_id) if user.tenant_id else None}
    access = create_access_token(identity=str(user.id), additional_claims=claims)
    refresh = create_refresh_token(identity=str(user.id), additional_claims=claims)
    return jsonify({"access_token": access, "refresh_token": refresh})

@bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    user_id = get_jwt_identity()
    user = User.objects.get(id=user_id)
    claims = {"role": user.role, "tenant_id": str(user.tenant_id) if user.tenant_id else None}
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
        "tenant_id": str(user.tenant_id) if user.tenant_id else None
    })

@bp.post("/register")
def register():
    # optional simple open registration (can be disabled in production)
    data = request.get_json(force=True, silent=True) or {}
    if not data.get("username") or not data.get("password"):
        return jsonify({"error": "username & password required"}), 400
    if User.objects(username=data["username"]).first():
        return jsonify({"error": "username exists"}), 409
    u = User(
        username=data["username"],
        email=data.get("email"),
        role=data.get("role","user")
    )
    u.set_password(data["password"])
    u.save()
    return jsonify({"id": str(u.id), "username": u.username}), 201
