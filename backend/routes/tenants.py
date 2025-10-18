# backend/routes/tenants.py
from flask import Blueprint, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity

# Imports opcionais (compatível com os teus modelos)
try:
    from models.tenant import Tenant  # type: ignore
except Exception:  # pragma: no cover
    Tenant = None  # type: ignore

try:
    from models.laboratory import Laboratory  # type: ignore
except Exception:  # pragma: no cover
    Laboratory = None  # type: ignore

try:
    from models.user import User  # type: ignore
except Exception:  # pragma: no cover
    User = None  # type: ignore

bp = Blueprint("tenants", __name__, url_prefix="/api/tenants")

def _doc_to_tenant(doc) -> dict:
    """Normaliza qualquer doc para {id, _id, name}."""
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

def _load_tenants_for_user(user) -> list[dict]:
    """Devolve a lista de tenants visíveis para o utilizador.

    Regra:
    - Sysadmin → todos os Laboratory
    - Não-sysadmin → apenas `allowed_labs` + `tenant_id` (se existir)
    """
    items: list[dict] = []

    if Laboratory is None or user is None:
        return [{"id": "default", "_id": "default", "name": "Default"}]

    try:
        if getattr(user, "is_sysadmin", False):
            qs = Laboratory.objects  # type: ignore[attr-defined]
        else:
            allowed_ids = []
            try:
                allowed_ids = [
                    str(getattr(x, "id", ""))
                    for x in ((getattr(user, "allowed_labs", []) or []))
                    if getattr(x, "id", None)
                ]
            except Exception:
                allowed_ids = []
            # incluir tenant_id atual se existir e não estiver na lista
            tid = str(getattr(getattr(user, "tenant_id", None), "id", "") or "")
            if tid and tid not in allowed_ids:
                allowed_ids.append(tid)
            if allowed_ids:
                qs = Laboratory.objects(id__in=allowed_ids)  # type: ignore[attr-defined]
            else:
                qs = Laboratory.objects.none()  # type: ignore[attr-defined]
        for lab in qs:  # type: ignore
            items.append(_doc_to_tenant(lab))
    except Exception as e:  # pragma: no cover
        current_app.logger.warning("Falha a listar tenants para utilizador: %s", e)
        items = []

    if not items:
        items = [{"id": "default", "_id": "default", "name": "Default"}]
    return items

# Aceita /api/tenants (sem barra) e /api/tenants/ (com barra)
@bp.get("")
@bp.get("/")
@jwt_required()
def list_tenants():
    """
    GET /api/tenants
    Devolve a lista de tenants que o utilizador pode ver.
    Responde com um ARRAY para bater certo com o frontend.
    """
    # Carrega utilizador para aplicar scoping por permissões
    user = None
    try:
        uid = get_jwt_identity()
        if User is not None and uid is not None:
            user = User.objects.get(id=uid)  # type: ignore[attr-defined]
    except Exception:
        user = None

    items = _load_tenants_for_user(user)

    # Opcional: mover o tenant_id do JWT para o topo
    try:
        claims = get_jwt() or {}
        tid = claims.get("tenant_id")
        if tid:
            items.sort(key=lambda it: 0 if it.get("id") == str(tid) else 1)
    except Exception:
        pass

    # devolvemos um array simples
    return jsonify(items)

# Alias útil se o frontend estiver a chamar /api/tenants/list
@bp.get("/list")
@jwt_required()
def list_tenants_alias():
    return list_tenants()
