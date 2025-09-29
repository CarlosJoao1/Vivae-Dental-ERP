# backend/routes/tenants.py
from flask import Blueprint, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt

# Imports opcionais (compatível com os teus modelos)
try:
    from models.tenant import Tenant  # type: ignore
except Exception:  # pragma: no cover
    Tenant = None  # type: ignore

try:
    from models.laboratory import Laboratory  # type: ignore
except Exception:  # pragma: no cover
    Laboratory = None  # type: ignore

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

def _load_all_tenants() -> list[dict]:
    """Devolve uma lista de tenants a partir dos modelos disponíveis."""
    items: list[dict] = []

    # Preferência: Tenant, se existir
    if Tenant:
        try:
            for t in Tenant.objects:  # type: ignore[attr-defined]
                items.append(_doc_to_tenant(t))
        except Exception as e:  # pragma: no cover
            current_app.logger.warning("Falha a listar Tenant: %s", e)

    # Alternativa: Laboratory (o seed cria um)
    if not items and Laboratory:
        try:
            for lab in Laboratory.objects:  # type: ignore[attr-defined]
                items.append(_doc_to_tenant(lab))
        except Exception as e:  # pragma: no cover
            current_app.logger.warning("Falha a listar Laboratory: %s", e)

    # Fallback final
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
    items = _load_all_tenants()

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
