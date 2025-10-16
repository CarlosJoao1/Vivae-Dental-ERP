# backend/routes/auth.py
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    jwt_required, create_access_token, create_refresh_token, get_jwt_identity
)
from models.user import User
from mongoengine.errors import DoesNotExist
import json, base64

# Imports opcionais para montar a lista de tenants em /me
try:
    from models.tenant import Tenant  # type: ignore
except Exception:
    Tenant = None  # type: ignore
try:
    from models.laboratory import Laboratory  # type: ignore
except Exception:
    Laboratory = None  # type: ignore

bp = Blueprint("auth", __name__, url_prefix="/api/auth")

def _parse_json_body() -> dict:
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

def _doc_to_tenant(doc) -> dict:
    if not doc:
        return {"id": "default", "_id": "default", "name": "Default"}
    doc_id = str(getattr(doc, "id", "default"))
    name = (
        getattr(doc, "name", None)
        or getattr(doc, "title", None)
        or getattr(doc, "label", None)
        or "Tenant"
    )
    return {"id": doc_id, "_id": doc_id, "name": name}

def _resolve_tenants_for_user(user: User):
    items = []
    # Se existir um modelo Tenant, carrega todos (ou filtra como precisares)
    if Tenant:
        try:
            qs = Tenant.objects  # type: ignore[attr-defined]
            for t in qs:
                items.append(_doc_to_tenant(t))
        except Exception as e:
            current_app.logger.warning("Falha a listar Tenant: %s", e)

    # Caso não haja Tenant, usa Laboratory (o seed cria um)
    if not items and Laboratory:
        try:
            qs = Laboratory.objects  # type: ignore[attr-defined]
            for lab in qs:
                items.append(_doc_to_tenant(lab))
        except Exception as e:
            current_app.logger.warning("Falha a listar Laboratory: %s", e)

    # Se mesmo assim nada, devolve um default
    if not items:
        items = [{"id": "default", "_id": "default", "name": "Default"}]

    # Se o utilizador tiver tenant_id, tenta pô-lo como o primeiro da lista
    try:
        # Normaliza para ObjectId string quando for ReferenceField
        tid = str(getattr(getattr(user, "tenant_id", None), "id", "") or "")
        if tid:
            items.sort(key=lambda it: 0 if it.get("id") == tid else 1)
    except Exception:
        pass

    return items

@bp.post("/login")
def login():
    try:
        current_app.logger.info("Login attempt - Content-Type: %s", request.headers.get("Content-Type"))
        username, password = _get_credentials()
        
        if not username or not password:
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
            current_app.logger.warning("Login failed: user not found - %s", username)
            return jsonify({"error": "invalid credentials"}), 401

        if not user.check_password(password):
            current_app.logger.warning("Login failed: invalid password - %s", username)
            return jsonify({"error": "invalid credentials"}), 401

        # Claims com tenant_id normalizado para ObjectId string
        lab_id = str(getattr(getattr(user, "tenant_id", None), "id", "") or "")
        claims = {"role": user.role, "tenant_id": lab_id or None}
        access = create_access_token(identity=str(user.id), additional_claims=claims)
        refresh = create_refresh_token(identity=str(user.id), additional_claims=claims)

        # Opcional: já devolver tenants no login (útil para o AuthContext)
        tenants = _resolve_tenants_for_user(user)

        current_app.logger.info("Login successful for user: %s", username)
        return jsonify({"access_token": access, "refresh_token": refresh, "tenants": tenants})
    
    except Exception as e:
        current_app.logger.exception("Login error: %s", str(e))
        return jsonify({"error": "internal server error", "details": str(e)}), 500

@bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    user_id = get_jwt_identity()
    user = User.objects.get(id=user_id)
    lab_id = str(getattr(getattr(user, "tenant_id", None), "id", "") or "")
    claims = {"role": user.role, "tenant_id": lab_id or None}
    access = create_access_token(identity=str(user.id), additional_claims=claims)
    return jsonify({"access_token": access})

@bp.get("/me")
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = User.objects.get(id=user_id)
    # Enriquecemos com `tenants` para o frontend ter tudo num só request
    tenants = _resolve_tenants_for_user(user)
    return jsonify({
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "tenant_id": str(user.tenant_id) if user.tenant_id else None,
        "tenants": tenants,
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
        role=data.get("role","user")
    )
    u.set_password(password)
    u.save()
    return jsonify({"id": str(u.id), "username": u.username}), 201
