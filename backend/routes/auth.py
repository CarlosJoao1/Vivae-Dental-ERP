# backend/routes/auth.py
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    jwt_required, create_access_token, create_refresh_token, get_jwt_identity
)
from models.user import User
from models.laboratory import Laboratory
from mongoengine.errors import DoesNotExist
import json, base64
from models.role_policy import RolePolicy
from mongoengine.queryset.visitor import Q

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
            if getattr(user, "is_sysadmin", False):
                qs = Laboratory.objects  # type: ignore[attr-defined]
            else:
                # limit to user's allowed labs, fallback to tenant_id if present
                allowed_ids = []
                try:
                    allowed_ids = [str(getattr(x, 'id', '')) for x in (getattr(user, 'allowed_labs', []) or []) if getattr(x, 'id', None)]
                except Exception:
                    allowed_ids = []
                if getattr(user, 'tenant_id', None):
                    tid = str(getattr(getattr(user, 'tenant_id', None), 'id', '') or '')
                    if tid and tid not in allowed_ids:
                        allowed_ids.append(tid)
                if allowed_ids:
                    qs = Laboratory.objects(id__in=allowed_ids)  # type: ignore[attr-defined]
                else:
                    qs = Laboratory.objects.none()  # type: ignore[attr-defined]
            for lab in qs:  # type: ignore
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

def _lab_from_header_or_user(user):
    """Resolve active lab from X-Tenant-Id header if user has access; otherwise user's tenant_id."""
    tid = (request.headers.get("X-Tenant-Id") or "").strip()
    if tid:
        try:
            if getattr(user, 'is_sysadmin', False):
                return Laboratory.objects.get(id=tid)
            allowed_ids = [str(getattr(x, 'id', '')) for x in (getattr(user, 'allowed_labs', []) or [])]
            if tid in allowed_ids:
                return Laboratory.objects.get(id=tid)
        except Exception:
            return None
    return getattr(user, 'tenant_id', None)

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

        # Guarantee default admin has sysadmin privileges (no-restart upgrade)
        try:
            if (user.username or "").lower() == "admin" and not getattr(user, "is_sysadmin", False):
                user.role = "sysadmin"
                user.save()
                current_app.logger.info("Auto-upgraded 'admin' user to sysadmin on login")
        except Exception as _:
            pass

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
    # Resolve active lab (header override allowed if permitted) to compute permissions
    header_tid = (request.headers.get("X-Tenant-Id") or "").strip()
    active_lab = None
    if header_tid:
        try:
            if getattr(user, 'is_sysadmin', False):
                active_lab = Laboratory.objects.get(id=header_tid)
            else:
                allowed_ids = [str(getattr(x, 'id', '')) for x in (getattr(user, 'allowed_labs', []) or [])]
                if header_tid in allowed_ids:
                    active_lab = Laboratory.objects.get(id=header_tid)
        except Exception:
            active_lab = None
    if not active_lab and getattr(user, 'tenant_id', None):
        active_lab = user.tenant_id
    # Compute role-based feature permissions for current role and active lab
    permissions = {}
    try:
        if getattr(user, 'is_sysadmin', False):
            permissions = {"__role__": "sysadmin", "all": True}
        elif active_lab is not None:
            rp = RolePolicy.objects(lab=active_lab).first()
            role = (user.role or '').lower()
            permissions = (rp.policies or {}).get(role, {}) if rp else {}
    except Exception:
        permissions = {}
    return jsonify({
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "is_sysadmin": bool(getattr(user, 'is_sysadmin', False)),
        "tenant_id": str(user.tenant_id) if user.tenant_id else None,
        "allowed_labs": [str(getattr(x, 'id', '')) for x in (getattr(user, 'allowed_labs', []) or [])],
        "tenants": tenants,
        "permissions": permissions,
    })


@bp.get("/stats")
@jwt_required()
def stats():
    """Return basic auth-related stats for the dashboard.

    - tenants_accessible: how many tenants this user can see (not global total)
    - total_users: total users in system (sysadmin visibility), else None for non-sysadmin
    - users_in_tenant: users assigned/allowed to the active tenant (header override allowed)
    """
    try:
        uid = get_jwt_identity()
        user = User.objects.get(id=uid)
        tenants = _resolve_tenants_for_user(user)
        tenants_accessible = len(tenants or [])
        lab = _lab_from_header_or_user(user)
        users_in_tenant = None
        if lab is not None:
            try:
                users_in_tenant = User.objects(Q(tenant_id=lab) | Q(allowed_labs=lab)).count()
            except Exception:
                users_in_tenant = 0
        total_users = None
        try:
            if getattr(user, 'is_sysadmin', False):
                total_users = User.objects.count()
        except Exception:
            total_users = None
        return jsonify({
            "tenants_accessible": int(tenants_accessible),
            "users_in_tenant": int(users_in_tenant) if users_in_tenant is not None else None,
            "total_users": int(total_users) if total_users is not None else None,
        })
    except Exception as e:
        current_app.logger.warning("/auth/stats error: %s", e)
        return jsonify({
            "tenants_accessible": 0,
            "users_in_tenant": None,
            "total_users": None,
        })

@bp.post("/register")
@jwt_required()
def register():
    data = _parse_json_body()
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return jsonify({"error": "username & password required"}), 400
    if User.objects(username=username).first():
        return jsonify({"error": "username exists"}), 409
    # Optional tenant_id
    tenant_id = (data.get("tenant_id") or data.get("lab_id") or "").strip()
    lab = None
    if tenant_id:
        try:
            lab = Laboratory.objects.get(id=tenant_id)
        except Exception:
            return jsonify({"error": "invalid tenant_id"}), 400
    # Permission rules: only sysadmin can create sysadmin; non-sysadmin can only create users for labs they can access.
    creator_id = get_jwt_identity()
    creator = User.objects.get(id=creator_id)
    role = (data.get("role") or "user").lower()
    if not getattr(creator, "is_sysadmin", False):
        # Non-sysadmin cannot assign sysadmin role
        if role == "sysadmin":
            return jsonify({"error": "not allowed to assign sysadmin"}), 403
        # Non-sysadmin can only create in allowed labs
        if lab:
            allowed_ids = [str(getattr(x, 'id', '')) for x in (getattr(creator, 'allowed_labs', []) or [])]
            # Must be both allowed AND equal to current selected tenant in JWT
            current_tid = str(getattr(getattr(creator, 'tenant_id', None), 'id', '') or '')
            if str(getattr(lab, 'id', '')) not in allowed_ids or str(getattr(lab, 'id', '')) != current_tid:
                return jsonify({"error": "not allowed for this lab / wrong active tenant"}), 403

    u = User(
        username=username,
        email=data.get("email"),
        role=role,
        tenant_id=lab,
    )
    u.set_password(password)
    # Manage allowed_labs: sysadmin ignored; for others, initialize allowed_labs with provided tenant if present
    try:
        if not getattr(u, "is_sysadmin", False):
            if lab:
                u.allowed_labs = [lab]
    except Exception:
        pass
    u.save()
    return jsonify({"id": str(u.id), "username": u.username, "tenant_id": str(getattr(lab,'id','')) or None}), 201


@bp.get("/preferences")
@jwt_required()
def get_preferences():
    """Return current user's stored preferences (UI, etc.)."""
    try:
        uid = get_jwt_identity()
        user = User.objects.get(id=uid)
        prefs = getattr(user, "preferences", {}) or {}
        return jsonify({"preferences": prefs})
    except Exception as e:
        current_app.logger.warning("get_preferences failed: %s", e)
        return jsonify({"preferences": {}})


@bp.put("/preferences")
@jwt_required()
def update_preferences():
    """Merge and persist preferences for current user."""
    try:
        uid = get_jwt_identity()
        user = User.objects.get(id=uid)
        data = request.get_json(silent=True, force=True) or {}
        incoming = data.get("preferences") if isinstance(data, dict) else None
        if not isinstance(incoming, dict):
            return jsonify({"error": "invalid preferences"}), 400
        base = dict(getattr(user, "preferences", {}) or {})
        base.update(incoming)
        user.preferences = base
        user.save()
        return jsonify({"preferences": base})
    except Exception as e:
        current_app.logger.exception("update_preferences error: %s", e)
        return jsonify({"error": "failed to update preferences"}), 500


def _sysadmin_required() -> User:
    """Helper to fetch current user and ensure sysadmin role."""
    uid = get_jwt_identity()
    user = User.objects.get(id=uid)
    if not getattr(user, 'is_sysadmin', False):
        raise PermissionError("not allowed")
    return user


@bp.get("/users")
@jwt_required()
def list_users():
    try:
        _sysadmin_required()
        users = User.objects.order_by("username")
        def u_to_dict(u: User):
            return {
                "id": str(u.id),
                "username": u.username,
                "email": u.email,
                "role": u.role,
                "tenant_id": str(getattr(getattr(u, 'tenant_id', None), 'id', '')) or None,
                "allowed_labs": [str(getattr(x, 'id', '')) for x in (getattr(u, 'allowed_labs', []) or [])],
            }
        return jsonify({"items": [u_to_dict(u) for u in users]})
    except PermissionError:
        return jsonify({"error": "not allowed"}), 403
    except Exception as e:
        current_app.logger.exception("list_users error: %s", e)
        return jsonify({"error": "failed"}), 500


@bp.put("/users/<uid>/allowed-labs")
@jwt_required()
def update_user_allowed_labs(uid):
    try:
        _sysadmin_required()
        data = request.get_json(force=True, silent=True) or {}
        lab_ids = data.get("lab_ids") or []
        if not isinstance(lab_ids, list):
            return jsonify({"error": "lab_ids must be list"}), 400
        labs = []
        for lid in lab_ids:
            try:
                labs.append(Laboratory.objects.get(id=str(lid)))
            except Exception:
                return jsonify({"error": f"invalid lab id {lid}"}), 400
        u = User.objects.get(id=uid)
        u.allowed_labs = labs
        # ensure tenant_id remains valid; if not, clear it
        try:
            if getattr(u, 'tenant_id', None) and all(str(getattr(x,'id','')) != str(getattr(getattr(u,'tenant_id',None),'id','')) for x in labs):
                u.tenant_id = None
        except Exception:
            pass
        u.save()
        return jsonify({"ok": True})
    except DoesNotExist:
        return jsonify({"error": "not found"}), 404
    except PermissionError:
        return jsonify({"error": "not allowed"}), 403
    except Exception as e:
        current_app.logger.exception("update_user_allowed_labs error: %s", e)
        return jsonify({"error": "failed"}), 500


@bp.put("/users/<uid>/role")
@jwt_required()
def update_user_role(uid):
    try:
        _sysadmin_required()
        data = request.get_json(force=True, silent=True) or {}
        role = (data.get("role") or "").strip().lower()
        if not role:
            return jsonify({"error": "role required"}), 400
        if role == "sysadmin":
            return jsonify({"error": "not allowed to assign sysadmin"}), 403
        u = User.objects.get(id=uid)
        # Protect existing sysadmin from being changed here (optional policy)
        if getattr(u, 'is_sysadmin', False):
            return jsonify({"error": "cannot change sysadmin role"}), 403
        u.role = role
        u.save()
        return jsonify({"ok": True})
    except DoesNotExist:
        return jsonify({"error": "not found"}), 404
    except PermissionError:
        return jsonify({"error": "not allowed"}), 403
    except Exception as e:
        current_app.logger.exception("update_user_role error: %s", e)
        return jsonify({"error": "failed"}), 500


@bp.put("/users/<uid>/tenant")
@jwt_required()
def update_user_tenant(uid):
    try:
        _sysadmin_required()
        data = request.get_json(force=True, silent=True) or {}
        tenant_id = (data.get("tenant_id") or "").strip()
        u = User.objects.get(id=uid)
        if not tenant_id:
            u.tenant_id = None
            u.save()
            return jsonify({"ok": True})
        try:
            lab = Laboratory.objects.get(id=tenant_id)
        except Exception:
            return jsonify({"error": "invalid tenant_id"}), 400
        # Validate tenant_id within user's allowed_labs
        allowed_ids = [str(getattr(x, 'id', '')) for x in (getattr(u, 'allowed_labs', []) or [])]
        if str(getattr(lab, 'id', '')) not in allowed_ids:
            return jsonify({"error": "tenant not in allowed_labs"}), 400
        u.tenant_id = lab
        u.save()
        return jsonify({"ok": True})
    except DoesNotExist:
        return jsonify({"error": "not found"}), 404
    except PermissionError:
        return jsonify({"error": "not allowed"}), 403
    except Exception as e:
        current_app.logger.exception("update_user_tenant error: %s", e)
        return jsonify({"error": "failed"}), 500
