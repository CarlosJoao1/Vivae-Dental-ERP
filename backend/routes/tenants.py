# backend/routes/tenants.py
from flask import Blueprint, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

# Imports opcionais (tentamos ambos para ser compatível com o teu modelo)
try:
    from models.tenant import Tenant  # type: ignore
except Exception:  # pragma: no cover
    Tenant = None  # type: ignore

try:
    from models.laboratory import Laboratory  # type: ignore
except Exception:  # pragma: no cover
    Laboratory = None  # type: ignore

try:
    from models.user import User
except Exception:  # pragma: no cover
    User = None  # type: ignore

bp = Blueprint("tenants", __name__, url_prefix="/api/tenants")

def _doc_to_tenant(doc) -> dict:
    """Normaliza qualquer doc para {id, _id, name}."""
    if not doc:
        return {"id": "default", "_id": "default", "name": "Default"}
    doc_id = str(getattr(doc, "id", "default"))
    # tenta vários campos comuns
    name = (
        getattr(doc, "name", None)
        or getattr(doc, "title", None)
        or getattr(doc, "label", None)
        or "Tenant"
    )
    return {"id": doc_id, "_id": doc_id, "name": name}

def _load_all_tenants():
    """Devolve uma lista de tenants a partir dos modelos disponíveis."""
    items = []
    # Preferência: Tenant, se existir
    if Tenant:
        try:
            qs = Tenant.objects  # type: ignore[attr-defined]
            for t in qs:  # type: ignore[assignment]
                items.append(_doc_to_tenant(t))
        except Exception as e:  # pragma: no cover
            current_app.logger.warning("Falha a listar Tenant: %s", e)

    # Alternativa: Laboratory (o seed cria um)
    if not items and Laboratory:
        try:
            qs = Laboratory.objects  # type: ignore[attr-defined]
            for lab in qs:  # type: ignore[assignment]
                items.append(_doc_to_tenant(lab))
        except Exception as e:  # pragma: no cover
            current_app.logger.warning("Falha a listar Laboratory: %s", e)

    # Fallback final
    if not items:
        items = [{"id": "default", "_id": "default", "name": "Default"}]

    return items

@bp.get("/")
@jwt_required()
def list_tenants():
    """
    GET /api/tenants
    Devolve a lista de tenants que o utilizador pode ver.
    Implementação simples: devolve todos (ou o Laboratory seed).
    """
    _ = get_jwt_identity()  # reservado para futura filtragem por utilizador
    tenants = _load_all_tenants()
    return jsonify({"items": tenants})

# Alias útil se o frontend estiver a chamar /api/tenants/list
@bp.get("/list")
@jwt_required()
def list_tenants_alias():
    return list_tenants()
