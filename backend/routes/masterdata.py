# backend/routes/masterdata.py
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from mongoengine.errors import ValidationError, DoesNotExist
from mongoengine.queryset.visitor import Q
from typing import Tuple
from datetime import date, datetime

from models.laboratory import Laboratory
from models.user import User
from models.patient import Patient
from models.technician import Technician
from models.service import Service
from models.document_type import DocumentType
from models.client import Client
from models.currency import Currency
from models.payment_type import PaymentType
from models.payment_form import PaymentForm
from models.payment_method import PaymentMethod
from models.series import Series
from models.country import Country
from models.shipping_address import ShippingAddress
from models.smtp_config import SmtpConfig
from models.client_price import ClientPrice
import smtplib
from email.message import EmailMessage
import socket
import os
from services.permissions import ensure

# Constants for error messages
ERR_NOT_FOUND = ERR_NOT_FOUND
ERR_CLIENT_EXISTS = "client exists"
ERR_INVALID_COUNTRY_CODE = ERR_INVALID_COUNTRY_CODE
ERROR_CLIENT_NOT_FOUND = "client not found"
ERROR_ADDRESS_EXISTS = "address exists"

bp = Blueprint("masterdata", __name__, url_prefix="/api/masterdata")

# --- Helpers ---

def _pagination() -> Tuple[int, int]:
    page = max(1, int(request.args.get("page", 1) or 1))
    size = min(100, max(1, int(request.args.get("page_size", 20) or 20)))
    return page, size

def _q() -> str:
    return (request.args.get("q", "") or "").strip()


def _lab() -> Laboratory:
    """Resolve active lab with header override (X-Tenant-Id) respecting permissions.

    Priority:
      1) If X-Tenant-Id header present and user allowed (or sysadmin), use it.
      2) Else use tenant_id claim from JWT.
      3) Else fallback to first lab (create default if missing).
    """
    # Header override when permitted
    try:
        uid = get_jwt_identity()
    except Exception:
        uid = None
    header_tid = (request.headers.get("X-Tenant-Id") or "").strip()
    if uid and header_tid:
        try:
            user = User.objects.get(id=uid)
            if getattr(user, 'is_sysadmin', False):
                return Laboratory.objects.get(id=header_tid)
            allowed_ids = [str(getattr(x, 'id', '')) for x in (getattr(user, 'allowed_labs', []) or [])]
            if header_tid in allowed_ids:
                return Laboratory.objects.get(id=header_tid)
        except Exception:
            pass
    # JWT tenant_id
    claims = get_jwt() or {}
    tid = claims.get("tenant_id")
    try:
        if tid and tid != "default":
            return Laboratory.objects.get(id=tid)
    except Exception as e:
        current_app.logger.warning("tenant_id inválido no JWT: %s", e)
    # fallback
    lab = Laboratory.objects.first()
    if not lab:
        lab = Laboratory(name="Default Lab").save()
    return lab

def _age_from_birthdate(dt) -> int | None:
    try:
        if not dt:
            return None
        # Accept both date and str
        b = _parse_date(dt)
        if not b:
            return None
        today = date.today()
        years = today.year - b.year - ((today.month, today.day) < (b.month, b.day))
        return years
    except Exception:
        return None

# --- Date helpers ---
def _parse_date(val) -> date | None:
    """Parse various date-like inputs to a date object.

    Accepts:
      - date -> returns as-is
      - datetime -> returns .date()
      - str (YYYY-MM-DD or ISO) -> parsed to date
      - empty/None -> None
    """
    if val is None:
        return None
    if isinstance(val, date) and not isinstance(val, datetime):
        return val
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, str):
        s = val.strip()
        if not s:
            return None
        # Try ISO date first, also tolerate full ISO datetime by slicing first 10 chars
        try:
            if len(s) >= 10:
                return date.fromisoformat(s[:10])
        except Exception:
            pass
        # Try common alt formats
        for fmt in ("%d/%m/%Y", "%Y/%m/%d", "%d-%m-%Y"):
            try:
                return datetime.strptime(s, fmt).date()
            except Exception:
                continue
        return None
    return None

def _date_to_iso(val) -> str | None:
    """Serialize date/datetime or pre-existing string to ISO date string (YYYY-MM-DD)."""
    if not val:
        return None
    if isinstance(val, str):
        # Assume already a date-like string
        s = val.strip()
        return s or None
    if isinstance(val, datetime):
        return val.date().isoformat()
    if isinstance(val, date):
        return val.isoformat()
    # Unknown type
    try:
        # last resort: attempt parse then iso
        d = _parse_date(val)
        return d.isoformat() if d else None
    except Exception:
        return None

def _dt_to_iso(val) -> str | None:
    """Serialize datetime-like value to full ISO 8601 string if possible, falling back to date-only when needed."""
    if not val:
        return None
    if isinstance(val, str):
        s = val.strip()
        return s or None
    if isinstance(val, datetime):
        try:
            return val.isoformat()
        except Exception:
            return None
    if isinstance(val, date):
        return val.isoformat()
    try:
        # No reliable parse to datetime; attempt parse to date
        d = _parse_date(val)
        return d.isoformat() if d else None
    except Exception:
        return None

# --- Serializers ---

def _lab_to_dict(l: Laboratory):
    return {
        "id": str(l.id),
        "name": l.name,
        "address": l.address or "",
        "country": l.country or "",
        "postal_code": l.postal_code or "",
        "city": l.city or "",
        "tax_id": l.tax_id or "",
        "phone": l.phone or "",
        "email": l.email or "",
        "logo_url": getattr(l, 'logo_url', '') or "",
        "active": bool(getattr(l, "active", True)),
    }

def _patient_to_dict(p: Patient):
    return {
        "id": str(p.id),
        "lab_id": str(getattr(p.lab, "id", "")),
        "name": p.name,
        "first_name": getattr(p, "first_name", None),
        "last_name": getattr(p, "last_name", None),
        "gender": getattr(p, "gender", None),
        "birthdate": _date_to_iso(getattr(p, "birthdate", None)),
        "age": _age_from_birthdate(getattr(p, "birthdate", None)),
        "email": p.email or "",
        "phone": p.phone or "",
        "address": getattr(p, "address", "") or "",
        "notes": p.notes or "",
    "created_at": _dt_to_iso(getattr(p, "created_at", None)),
    }

def _technician_to_dict(t: Technician):
    return {
        "id": str(t.id),
        "lab_id": str(getattr(t.lab, "id", "")),
        "name": t.name,
        "email": t.email or "",
        "phone": t.phone or "",
        "workcenter": t.workcenter or "",
    }

def _service_to_dict(s: Service):
    price = None
    try:
        price = float(s.price) if s.price is not None else None
    except Exception:
        price = None
    return {
        "id": str(s.id),
        "lab_id": str(getattr(s.lab, "id", "")),
        "name": s.name,
        "code": s.code or "",
        "price": price,
        "description": s.description or "",
    }

def _doctype_to_dict(d: DocumentType):
    return {
        "id": str(d.id),
        "lab_id": str(getattr(d.lab, "id", "")),
        "name": d.name,
        "extension": d.extension or "",
    }

def _client_to_dict(c: Client):
    return {
        "id": str(c.id),
        "lab_id": str(getattr(c.lab, "id", "")),
        "code": getattr(c, 'code', None),
        "name": c.name,
        "first_name": getattr(c, "first_name", None),
        "last_name": getattr(c, "last_name", None),
        "gender": getattr(c, "gender", None),
    "birthdate": _date_to_iso(getattr(c, "birthdate", None)),
    "age": _age_from_birthdate(getattr(c, "birthdate", None)),
        "email": c.email or "",
        "phone": c.phone or "",
        "address": getattr(c, "address", "") or "",
    "postal_code": getattr(c, "postal_code", "") or "",
    "country_code": getattr(c, "country_code", "") or "",
        "type": c.type or "",
        "tax_id": c.tax_id or "",
        "billing_address": c.billing_address or {},
        "shipping_address": c.shipping_address or {},
	"default_shipping_address": getattr(c, "default_shipping_address", "") or "",
        "payment_terms": c.payment_terms or "",
        "notes": c.notes or "",
        "active": bool(getattr(c, "active", True)),
        "contacts": c.contacts or [],
    "created_at": _dt_to_iso(getattr(c, "created_at", None)),
        # Financial preferences
        "preferred_currency": (
            {"id": str(getattr(c.preferred_currency, 'id', '')), "code": getattr(c.preferred_currency, 'code', None)}
            if getattr(c, 'preferred_currency', None) else None
        ),
        "payment_type": (
            {"id": str(getattr(c.payment_type, 'id', '')), "name": getattr(c.payment_type, 'name', None)}
            if getattr(c, 'payment_type', None) else None
        ),
        "payment_form": (
            {"id": str(getattr(c.payment_form, 'id', '')), "name": getattr(c.payment_form, 'name', None)}
            if getattr(c, 'payment_form', None) else None
        ),
        "payment_method": (
            {"id": str(getattr(c.payment_method, 'id', '')), "name": getattr(c.payment_method, 'name', None)}
            if getattr(c, 'payment_method', None) else None
        ),
    }

@bp.get("/clients/search")
@jwt_required()
def clients_search():
    lab = _lab()
    q = _q()
    qs = Client.objects(lab=lab)
    if q:
        qlc = q.lower()
        qs = qs.filter(
            (Q(name__icontains=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q) |
             Q(code__icontains=q) | Q(email__icontains=q) | Q(tax_id__icontains=q))
        )
    items = qs.order_by("name").limit(20)
    def brief(c: Client):
        full = (f"{getattr(c,'first_name','') or ''} {getattr(c,'last_name','') or ''}".strip() or c.name)
        return {
            "id": str(c.id),
            "code": getattr(c,'code', None),
            "name": full,
            "tax_id": getattr(c,'tax_id','') or '',
            "email": getattr(c,'email','') or '',
            "phone": getattr(c,'phone','') or '',
        }
    return jsonify({"items": [brief(x) for x in items]})

def _currency_to_dict(c: Currency):
    return {
        "id": str(c.id),
        "lab_id": str(getattr(c.lab, 'id', '')),
        "code": c.code,
        "name": c.name or "",
        "symbol": c.symbol or "",
        "is_default": bool(getattr(c, 'is_default', False)),
        "active": bool(getattr(c, 'active', True)),
    }

def _simple_fin_to_dict(o):
    return {
        "id": str(o.id),
        "lab_id": str(getattr(o.lab,'id','')),
        "code": getattr(o, 'code', None),
        "name": o.name,
        "active": bool(getattr(o,'active', True))
    }

def _series_to_dict(s: Series):
    return {
        "id": str(s.id),
        "lab_id": str(getattr(s.lab,'id','')),
        "doc_type": s.doc_type,
        "prefix": s.prefix or "",
        "next_number": s.next_number,
        "padding": s.padding,
        "active": bool(getattr(s,'active', True)),
    }

def _smtp_to_dict(cfg: SmtpConfig | None):
    if not cfg:
        return None
    return {
        "server": cfg.server,
        "port": cfg.port,
        "use_tls": bool(getattr(cfg, 'use_tls', False)),
        "use_ssl": bool(getattr(cfg, 'use_ssl', False)),
        "username": cfg.username or "",
        "has_password": bool(getattr(cfg, 'password', None)),
        # password omitted for security
    }

def _next_number(lab: Laboratory, doc_type: str, series_id: str | None, fallback_prefix: str) -> tuple[str, Series | None]:
    """Atomically increment series and return formatted number."""
    ser = None
    if series_id:
        try:
            ser = Series.objects.get(id=series_id, lab=lab, doc_type=doc_type)
        except Exception:
            ser = None
    if not ser:
        ser = Series.objects(lab=lab, doc_type=doc_type, active=True).first()
    if not ser:
        ser = Series(lab=lab, doc_type=doc_type, prefix=fallback_prefix, next_number=1, padding=5, active=True).save()
    Series.objects(id=ser.id).update_one(inc__next_number=1)
    ser.reload()
    num = ser.next_number - 1
    number = f"{ser.prefix}{num:0{ser.padding}d}"
    return number, ser

# --- Laboratories ---
@bp.get("/laboratories")
@jwt_required()
def labs_list():
    # Permission: laboratories.read
    try:
        uid = get_jwt_identity()
        from models.user import User  # local import to avoid circular
        user = User.objects.get(id=uid)
        err = ensure(user, None, 'laboratories', 'read')
        if err:
            return jsonify(err), 403
    except Exception:
        pass
    # Filter by user permissions: sysadmin sees all, others only their allowed_labs
    try:
        uid = get_jwt_identity()
        from models.user import User  # local import to avoid circular
        user = User.objects.get(id=uid)
        if getattr(user, 'is_sysadmin', False):
            labs = Laboratory.objects.order_by("name")
        else:
            allowed_ids = [getattr(x, 'id', None) for x in (getattr(user, 'allowed_labs', []) or []) if getattr(x, 'id', None)]
            # include tenant_id as implicit allowed
            if getattr(user, 'tenant_id', None):
                allowed_ids.append(getattr(user.tenant_id, 'id', None))
            if allowed_ids:
                labs = Laboratory.objects(id__in=allowed_ids).order_by("name")
            else:
                labs = Laboratory.objects.none()
    except Exception:
        labs = Laboratory.objects.none()
    return jsonify({"laboratories": [_lab_to_dict(x) for x in labs]})

@bp.post("/laboratories")
@jwt_required()
def labs_create():
    data = request.get_json(force=True, silent=True) or {}
    try:
        # Permission: laboratories.create (still requires sysadmin below)
        uid = get_jwt_identity()
        from models.user import User
        user = User.objects.get(id=uid)
        err = ensure(user, None, 'laboratories', 'create')
        if err:
            return jsonify(err), 403
        # Only sysadmin can create labs
        uid = get_jwt_identity()
        from models.user import User
        user = User.objects.get(id=uid)
        if not getattr(user, 'is_sysadmin', False):
            return jsonify({"error": "not allowed"}), 403
        lab = Laboratory(
            name=data.get("name"),
            address=data.get("address"),
            country=data.get("country"),
            postal_code=data.get("postal_code"),
            city=data.get("city"),
            tax_id=data.get("tax_id"),
            phone=data.get("phone"),
            email=data.get("email"),
            logo_url=data.get("logo_url"),
            active=data.get("active", True),
        ).save()
        return jsonify({"laboratory": _lab_to_dict(lab)}), 201
    except (ValidationError, Exception) as e:
        return jsonify({"error": str(e)}), 400

@bp.put("/laboratories/<lab_id>")
@jwt_required()
def labs_update(lab_id):
    data = request.get_json(force=True, silent=True) or {}
    try:
        # Permission: laboratories.update
        uid = get_jwt_identity()
        from models.user import User
        user = User.objects.get(id=uid)
        err = ensure(user, None, 'laboratories', 'update')
        if err:
            return jsonify(err), 403
        # Only sysadmin can update any lab; non-sysadmin only within allowed set
        uid = get_jwt_identity()
        from models.user import User
        user = User.objects.get(id=uid)
        if getattr(user, 'is_sysadmin', False):
            lab = Laboratory.objects.get(id=lab_id)
        else:
            allowed_ids = [getattr(x, 'id', None) for x in (getattr(user, 'allowed_labs', []) or []) if getattr(x, 'id', None)]
            if getattr(user, 'tenant_id', None):
                allowed_ids.append(getattr(user.tenant_id, 'id', None))
            lab = Laboratory.objects.get(id=lab_id, id__in=allowed_ids)
        for f in ["name","address","country","postal_code","city","tax_id","phone","email","logo_url","active"]:
            if f in data: setattr(lab, f, data[f])
        lab.save()
        return jsonify({"laboratory": _lab_to_dict(lab)})
    except DoesNotExist:
        return jsonify({"error": ERR_NOT_FOUND}), 404
    except (ValidationError, Exception) as e:
        return jsonify({"error": str(e)}), 400

# --- Patients ---
@bp.get("/patients")
@jwt_required()
def patients_list():
    lab = _lab()
    # Permission: patients.read
    try:
        uid = get_jwt_identity()
        user = User.objects.get(id=uid)
        err = ensure(user, lab, 'patients', 'read')
        if err:
            return jsonify(err), 403
    except Exception:
        pass
    page, size = _pagination()
    q = _q()
    qs = Patient.objects(lab=lab)
    if q:
        qs = qs.filter(name__icontains=q) | Patient.objects(lab=lab, first_name__icontains=q) | Patient.objects(lab=lab, last_name__icontains=q)
    total = qs.count()
    items = qs.order_by("name").skip((page-1)*size).limit(size)
    return jsonify({"total": total, "items": [_patient_to_dict(x) for x in items]})

@bp.post("/patients")
@jwt_required()
def patients_create():
    lab = _lab()
    # Permission: patients.create
    try:
        uid = get_jwt_identity()
        user = User.objects.get(id=uid)
        err = ensure(user, lab, 'patients', 'create')
        if err:
            return jsonify(err), 403
    except Exception:
        pass
    data = request.get_json(force=True, silent=True) or {}
    try:
        p = Patient(
            lab=lab,
            name=data.get("name") or (f"{data.get('first_name','').strip()} {data.get('last_name','').strip()}".strip() or None),
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            gender=data.get("gender"),
            birthdate=_parse_date(data.get("birthdate")),
            email=data.get("email"),
            phone=data.get("phone"),
            address=data.get("address"),
            notes=data.get("notes"),
        ).save()
        return jsonify({"patient": _patient_to_dict(p)}), 201
    except (ValidationError, Exception) as e:
        return jsonify({"error": str(e)}), 400

@bp.put("/patients/<pid>")
@jwt_required()
def patients_update(pid):
    lab = _lab()
    data = request.get_json(force=True, silent=True) or {}
    # Permission: patients.update
    try:
        uid = get_jwt_identity()
        user = User.objects.get(id=uid)
        err = ensure(user, lab, 'patients', 'update')
        if err:
            return jsonify(err), 403
    except Exception:
        pass
    try:
        p = Patient.objects.get(id=pid, lab=lab)
        # Normalize birthdate if present
        if "birthdate" in data:
            data["birthdate"] = _parse_date(data.get("birthdate"))
        for f in ["name","first_name","last_name","gender","birthdate","email","phone","address","notes"]:
            if f in data:
                setattr(p, f, data[f])
        # Atualiza name se não for fornecido mas first/last mudaram
        if not data.get("name") and ("first_name" in data or "last_name" in data):
            full = f"{getattr(p,'first_name','') or ''} {getattr(p,'last_name','') or ''}".strip()
            if full:
                p.name = full
        p.save()
        return jsonify({"patient": _patient_to_dict(p)})
    except DoesNotExist:
        return jsonify({"error": ERR_NOT_FOUND}), 404
    except (ValidationError, Exception) as e:
        return jsonify({"error": str(e)}), 400

@bp.delete("/patients/<pid>")
@jwt_required()
def patients_delete(pid):
    lab = _lab()
    # Permission: patients.delete
    try:
        uid = get_jwt_identity()
        user = User.objects.get(id=uid)
        err = ensure(user, lab, 'patients', 'delete')
        if err:
            return jsonify(err), 403
    except Exception:
        pass
    try:
        p = Patient.objects.get(id=pid, lab=lab)
        p.delete()
        return jsonify({"status": "deleted"})
    except DoesNotExist:
        return jsonify({"error": ERR_NOT_FOUND}), 404

# --- Technicians ---
@bp.get("/technicians")
@jwt_required()
def techs_list():
    lab = _lab()
    # Permission: technicians.read
    try:
        uid = get_jwt_identity()
        user = User.objects.get(id=uid)
        err = ensure(user, lab, 'technicians', 'read')
        if err:
            return jsonify(err), 403
    except Exception:
        pass
    page, size = _pagination()
    q = _q()
    qs = Technician.objects(lab=lab)
    if q:
        qs = qs.filter(name__icontains=q)
    total = qs.count()
    items = qs.order_by("name").skip((page-1)*size).limit(size)
    return jsonify({"total": total, "items": [_technician_to_dict(x) for x in items]})

@bp.post("/technicians")
@jwt_required()
def techs_create():
    lab = _lab()
    # Permission: technicians.create
    try:
        uid = get_jwt_identity()
        user = User.objects.get(id=uid)
        err = ensure(user, lab, 'technicians', 'create')
        if err:
            return jsonify(err), 403
    except Exception:
        pass
    data = request.get_json(force=True, silent=True) or {}
    try:
        t = Technician(
            lab=lab,
            name=data.get("name"),
            email=data.get("email"),
            phone=data.get("phone"),
            workcenter=data.get("workcenter"),
        ).save()
        return jsonify({"technician": _technician_to_dict(t)}), 201
    except (ValidationError, Exception) as e:
        return jsonify({"error": str(e)}), 400

@bp.put("/technicians/<tid>")
@jwt_required()
def techs_update(tid):
    lab = _lab()
    data = request.get_json(force=True, silent=True) or {}
    # Permission: technicians.update
    try:
        uid = get_jwt_identity()
        user = User.objects.get(id=uid)
        err = ensure(user, lab, 'technicians', 'update')
        if err:
            return jsonify(err), 403
    except Exception:
        pass
    try:
        t = Technician.objects.get(id=tid, lab=lab)
        for f in ["name","email","phone","workcenter"]:
            if f in data: setattr(t, f, data[f])
        t.save()
        return jsonify({"technician": _technician_to_dict(t)})
    except DoesNotExist:
        return jsonify({"error": ERR_NOT_FOUND}), 404
    except (ValidationError, Exception) as e:
        return jsonify({"error": str(e)}), 400

@bp.delete("/technicians/<tid>")
@jwt_required()
def techs_delete(tid):
    lab = _lab()
    # Permission: technicians.delete
    try:
        uid = get_jwt_identity()
        user = User.objects.get(id=uid)
        err = ensure(user, lab, 'technicians', 'delete')
        if err:
            return jsonify(err), 403
    except Exception:
        pass
    try:
        t = Technician.objects.get(id=tid, lab=lab)
        t.delete()
        return jsonify({"status": "deleted"})
    except DoesNotExist:
        return jsonify({"error": ERR_NOT_FOUND}), 404

# --- Services ---
@bp.get("/services")
@jwt_required()
def services_list():
    lab = _lab()
    # Permission: services.read
    try:
        uid = get_jwt_identity()
        user = User.objects.get(id=uid)
        err = ensure(user, lab, 'services', 'read')
        if err:
            return jsonify(err), 403
    except Exception:
        pass
    page, size = _pagination()
    q = _q()
    qs = Service.objects(lab=lab)
    if q:
        qs = qs.filter(name__icontains=q) | Service.objects(lab=lab, code__icontains=q)
    total = qs.count()
    items = qs.order_by("name").skip((page-1)*size).limit(size)
    return jsonify({"total": total, "items": [_service_to_dict(x) for x in items]})

@bp.post("/services")
@jwt_required()
def services_create():
    lab = _lab()
    # Permission: services.create
    try:
        uid = get_jwt_identity()
        user = User.objects.get(id=uid)
        err = ensure(user, lab, 'services', 'create')
        if err:
            return jsonify(err), 403
    except Exception:
        pass
    data = request.get_json(force=True, silent=True) or {}
    try:
        s = Service(
            lab=lab,
            name=data.get("name"),
            code=data.get("code"),
            price=data.get("price"),
            description=data.get("description"),
        ).save()
        return jsonify({"service": _service_to_dict(s)}), 201
    except (ValidationError, Exception) as e:
        return jsonify({"error": str(e)}), 400

@bp.put("/services/<sid>")
@jwt_required()
def services_update(sid):
    lab = _lab()
    data = request.get_json(force=True, silent=True) or {}
    # Permission: services.update
    try:
        uid = get_jwt_identity()
        user = User.objects.get(id=uid)
        err = ensure(user, lab, 'services', 'update')
        if err:
            return jsonify(err), 403
    except Exception:
        pass
    try:
        s = Service.objects.get(id=sid, lab=lab)
        for f in ["name","code","price","description"]:
            if f in data: setattr(s, f, data[f])
        s.save()
        return jsonify({"service": _service_to_dict(s)})
    except DoesNotExist:
        return jsonify({"error": ERR_NOT_FOUND}), 404
    except (ValidationError, Exception) as e:
        return jsonify({"error": str(e)}), 400

@bp.delete("/services/<sid>")
@jwt_required()
def services_delete(sid):
    lab = _lab()
    # Permission: services.delete
    try:
        uid = get_jwt_identity()
        user = User.objects.get(id=uid)
        err = ensure(user, lab, 'services', 'delete')
        if err:
            return jsonify(err), 403
    except Exception:
        pass
    try:
        s = Service.objects.get(id=sid, lab=lab)
        s.delete()
        return jsonify({"status": "deleted"})
    except DoesNotExist:
        return jsonify({"error": ERR_NOT_FOUND}), 404

# --- Document Types ---
@bp.get("/document-types")
@jwt_required()
def doctypes_list():
    lab = _lab()
    # Permission: document_types.read
    try:
        uid = get_jwt_identity()
        user = User.objects.get(id=uid)
        err = ensure(user, lab, 'document_types', 'read')
        if err:
            return jsonify(err), 403
    except Exception:
        pass
    page, size = _pagination()
    q = _q()
    qs = DocumentType.objects(lab=lab)
    if q:
        qs = qs.filter(name__icontains=q)
    total = qs.count()
    items = qs.order_by("name").skip((page-1)*size).limit(size)
    return jsonify({"total": total, "items": [_doctype_to_dict(x) for x in items]})

@bp.post("/document-types")
@jwt_required()
def doctypes_create():
    lab = _lab()
    # Permission: document_types.create
    try:
        uid = get_jwt_identity()
        user = User.objects.get(id=uid)
        err = ensure(user, lab, 'document_types', 'create')
        if err:
            return jsonify(err), 403
    except Exception:
        pass
    data = request.get_json(force=True, silent=True) or {}
    try:
        d = DocumentType(
            lab=lab,
            name=data.get("name"),
            extension=data.get("extension"),
        ).save()
        return jsonify({"document_type": _doctype_to_dict(d)}), 201
    except (ValidationError, Exception) as e:
        return jsonify({"error": str(e)}), 400

@bp.put("/document-types/<did>")
@jwt_required()
def doctypes_update(did):
    lab = _lab()
    data = request.get_json(force=True, silent=True) or {}
    # Permission: document_types.update
    try:
        uid = get_jwt_identity()
        user = User.objects.get(id=uid)
        err = ensure(user, lab, 'document_types', 'update')
        if err:
            return jsonify(err), 403
    except Exception:
        pass
    try:
        d = DocumentType.objects.get(id=did, lab=lab)
        for f in ["name","extension"]:
            if f in data: setattr(d, f, data[f])
        d.save()
        return jsonify({"document_type": _doctype_to_dict(d)})
    except DoesNotExist:
        return jsonify({"error": ERR_NOT_FOUND}), 404
    except (ValidationError, Exception) as e:
        return jsonify({"error": str(e)}), 400

@bp.delete("/document-types/<did>")
@jwt_required()
def doctypes_delete(did):
    lab = _lab()
    # Permission: document_types.delete
    try:
        uid = get_jwt_identity()
        user = User.objects.get(id=uid)
        err = ensure(user, lab, 'document_types', 'delete')
        if err:
            return jsonify(err), 403
    except Exception:
        pass
    try:
        d = DocumentType.objects.get(id=did, lab=lab)
        d.delete()
        return jsonify({"status": "deleted"})
    except DoesNotExist:
        return jsonify({"error": ERR_NOT_FOUND}), 404

# --- Clients ---
@bp.get("/clients")
@jwt_required()
def clients_list():
    lab = _lab()
    page, size = _pagination()
    q = _q()
    qs = Client.objects(lab=lab)
    if q:
        qs = qs.filter(name__icontains=q) | Client.objects(lab=lab, first_name__icontains=q) | Client.objects(lab=lab, last_name__icontains=q)
    total = qs.count()
    items = qs.order_by("name").skip((page-1)*size).limit(size)
    return jsonify({"total": total, "items": [_client_to_dict(x) for x in items]})

@bp.post("/clients")
@jwt_required()
def clients_create():
    lab = _lab()
    data = request.get_json(force=True, silent=True) or {}
    try:
        code = (data.get("code") or "").strip()
        # Auto-generate code if missing using client series
        if not code:
            code, _ = _next_number(lab, "client", data.get("series"), "CLI-")
        tax_id = (data.get("tax_id") or "").strip() or None
        email = (data.get("email") or "").strip() or None
        # Duplicate check (per lab)
        if Client.objects(lab=lab, code=code).first():
            return jsonify({"error": ERR_CLIENT_EXISTS, "field": "code"}), 409
        if tax_id and Client.objects(lab=lab, tax_id=tax_id).first():
            return jsonify({"error": ERR_CLIENT_EXISTS, "field": "tax_id"}), 409
        if email and Client.objects(lab=lab, email=email).first():
            return jsonify({"error": ERR_CLIENT_EXISTS, "field": "email"}), 409

        # Resolve references
        pc = None
        if data.get("preferred_currency"):
            try:
                pc = Currency.objects.get(id=data.get("preferred_currency"))
            except Exception:
                pc = None
        pt = pf = pm = None
        if data.get("payment_type"):
            try:
                pt = PaymentType.objects.get(id=data.get("payment_type"))
            except Exception:
                pt = None
        if data.get("payment_form"):
            try:
                pf = PaymentForm.objects.get(id=data.get("payment_form"))
            except Exception:
                pf = None
        if data.get("payment_method"):
            try:
                pm = PaymentMethod.objects.get(id=data.get("payment_method"))
            except Exception:
                pm = None

        # Validate country_code
        cc = (data.get("country_code") or '').upper() or None
        if cc and not Country.objects(code=cc).first():
            return jsonify({"error": ERR_INVALID_COUNTRY_CODE, "field": "country_code"}), 400
        # Validate default_shipping_address code exists for this client within lab
        dsa = (data.get("default_shipping_address") or '').strip()
        if dsa:
            # We will match after client is created; for now, allow only if belongs to target client when explicitly provided with client in shipping-address create
            # Since we don't have c yet, we will recheck right after creating c
            if not ShippingAddress.objects(lab=lab, code=dsa).first():
                return jsonify({"error": "invalid default_shipping_address", "field": "default_shipping_address"}), 400

        c = Client(
            lab=lab,
            code=code,
            name=data.get("name") or (f"{data.get('first_name','').strip()} {data.get('last_name','').strip()}".strip() or None),
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            gender=data.get("gender"),
            birthdate=_parse_date(data.get("birthdate")),
            email=email,
            phone=data.get("phone"),
            address=data.get("address"),
            postal_code=data.get("postal_code"),
            country_code=cc,
            type=data.get("type"),
            tax_id=tax_id,
            billing_address=data.get("billing_address"),
            shipping_address=data.get("shipping_address"),
            default_shipping_address=dsa or None,
            payment_terms=data.get("payment_terms"),
            notes=data.get("notes"),
            active=data.get("active", True),
            contacts=data.get("contacts") or [],
            preferred_currency=pc,
            payment_type=pt,
            payment_form=pf,
            payment_method=pm,
            location_code=data.get("location_code"),
        ).save()
        # Post-create: if default_shipping_address provided, ensure it belongs to this client; otherwise clear it
        if dsa:
            try:
                if not ShippingAddress.objects(lab=lab, client=c, code=dsa).first():
                    c.update(unset__default_shipping_address=1)
                    c.reload()
            except Exception:
                pass
        return jsonify({"client": _client_to_dict(c)}), 201
    except (ValidationError, Exception) as e:
        return jsonify({"error": str(e)}), 400

@bp.put("/clients/<cid>")
@jwt_required()
def clients_update(cid):
    lab = _lab()
    data = request.get_json(force=True, silent=True) or {}
    try:
        c = Client.objects.get(id=cid, lab=lab)
        # code duplicate check
        if "code" in data:
            new_code = (data.get("code") or "").strip()
            if not new_code:
                # keep current code if empty provided
                new_code = c.code
            dup = Client.objects(lab=lab, code=new_code, id__ne=c.id).first()
            if dup:
                return jsonify({"error": ERR_CLIENT_EXISTS, "field": "code"}), 409
        tax_id = (data.get("tax_id") if "tax_id" in data else c.tax_id) or None
        email = (data.get("email") if "email" in data else c.email) or None
        # Duplicate check excluding current
        if tax_id:
            dup = Client.objects(lab=lab, tax_id=tax_id, id__ne=c.id).first()
            if dup:
                return jsonify({"error": ERR_CLIENT_EXISTS, "field": "tax_id"}), 409
        if email:
            dup = Client.objects(lab=lab, email=email, id__ne=c.id).first()
            if dup:
                return jsonify({"error": ERR_CLIENT_EXISTS, "field": "email"}), 409

        # Normalize and validate country_code if present
        if 'country_code' in data:
            cc = (data.get('country_code') or '').upper() or None
            if cc and not Country.objects(code=cc).first():
                return jsonify({"error": ERR_INVALID_COUNTRY_CODE, "field": "country_code"}), 400
            data['country_code'] = cc
        # Validate default_shipping_address if present (must belong to this client)
        if 'default_shipping_address' in data:
            dsa = (data.get('default_shipping_address') or '').strip()
            if dsa and not ShippingAddress.objects(lab=lab, client=c, code=dsa).first():
                return jsonify({"error": "invalid default_shipping_address", "field": "default_shipping_address"}), 400
            data['default_shipping_address'] = dsa or None

        # Normalize birthdate if present
        if "birthdate" in data:
            data["birthdate"] = _parse_date(data.get("birthdate"))
        for f in [
            "code","name","first_name","last_name","gender","birthdate","email","phone","address","postal_code","country_code",
            "type","tax_id","billing_address","shipping_address","default_shipping_address","payment_terms","notes","active","contacts","location_code"
        ]:
            if f in data:
                setattr(c, f, data[f])
        # Refs
        if "preferred_currency" in data:
            try:
                c.preferred_currency = Currency.objects.get(id=data.get("preferred_currency")) if data.get("preferred_currency") else None
            except Exception:
                c.preferred_currency = None
        if "payment_type" in data:
            try:
                c.payment_type = PaymentType.objects.get(id=data.get("payment_type")) if data.get("payment_type") else None
            except Exception:
                c.payment_type = None
        if "payment_form" in data:
            try:
                c.payment_form = PaymentForm.objects.get(id=data.get("payment_form")) if data.get("payment_form") else None
            except Exception:
                c.payment_form = None
        if "payment_method" in data:
            try:
                c.payment_method = PaymentMethod.objects.get(id=data.get("payment_method")) if data.get("payment_method") else None
            except Exception:
                c.payment_method = None
        if not data.get("name") and ("first_name" in data or "last_name" in data):
            full = f"{getattr(c,'first_name','') or ''} {getattr(c,'last_name','') or ''}".strip()
            if full:
                c.name = full
        c.save()
        return jsonify({"client": _client_to_dict(c)})
    except DoesNotExist:
        return jsonify({"error": ERR_NOT_FOUND}), 404
    except (ValidationError, Exception) as e:
        return jsonify({"error": str(e)}), 400

@bp.delete("/clients/<cid>")
@jwt_required()
def clients_delete(cid):
    lab = _lab()
    try:
        c = Client.objects.get(id=cid, lab=lab)
        c.delete()
        return jsonify({"status": "deleted"})
    except DoesNotExist:
        return jsonify({"error": ERR_NOT_FOUND}), 404

# Single client
@bp.get("/clients/<cid>")
@jwt_required()
def clients_get(cid):
    lab = _lab()
    # Permission: clients.read (single)
    try:
        uid = get_jwt_identity()
        user = User.objects.get(id=uid)
        err = ensure(user, lab, 'clients', 'read')
        if err:
            return jsonify(err), 403
    except Exception:
        pass
    try:
        c = Client.objects.get(id=cid, lab=lab)
        return jsonify({"client": _client_to_dict(c)})
    except DoesNotExist:
        return jsonify({"error": ERR_NOT_FOUND}), 404

# --- Financial: Currencies ---
@bp.get("/financial/currencies")
@jwt_required()
def currencies_list():
    lab = _lab()
    items = Currency.objects(lab=lab).order_by("code")
    return jsonify({"items": [_currency_to_dict(x) for x in items]})

@bp.post("/financial/currencies")
@jwt_required()
def currencies_create():
    lab = _lab()
    data = request.get_json(force=True, silent=True) or {}
    c = Currency(lab=lab,
                 code=data.get('code'),
                 name=data.get('name'),
                 symbol=data.get('symbol'),
                 is_default=data.get('is_default', False),
                 active=data.get('active', True)).save()
    return jsonify({"currency": _currency_to_dict(c)}), 201

# --- Financial: Payment Types ---
@bp.get("/financial/payment-types")
@jwt_required()
def paytypes_list():
    lab = _lab()
    items = PaymentType.objects(lab=lab).order_by("name")
    return jsonify({"items": [_simple_fin_to_dict(x) for x in items]})

@bp.post("/financial/payment-types")
@jwt_required()
def paytypes_create():
    lab = _lab()
    data = request.get_json(force=True, silent=True) or {}
    obj = PaymentType(lab=lab,
                      code=data.get('code'),
                      name=data.get('name'),
                      active=data.get('active', True)).save()
    return jsonify({"payment_type": _simple_fin_to_dict(obj)}), 201

# --- Financial: Payment Forms ---
@bp.get("/financial/payment-forms")
@jwt_required()
def payforms_list():
    lab = _lab()
    items = PaymentForm.objects(lab=lab).order_by("name")
    return jsonify({"items": [_simple_fin_to_dict(x) for x in items]})

@bp.post("/financial/payment-forms")
@jwt_required()
def payforms_create():
    lab = _lab()
    data = request.get_json(force=True, silent=True) or {}
    obj = PaymentForm(lab=lab,
                      code=data.get('code'),
                      name=data.get('name'),
                      active=data.get('active', True)).save()
    return jsonify({"payment_form": _simple_fin_to_dict(obj)}), 201

# --- Financial: Payment Methods ---
@bp.get("/financial/payment-methods")
@jwt_required()
def paymethods_list():
    lab = _lab()
    items = PaymentMethod.objects(lab=lab).order_by("name")
    return jsonify({"items": [_simple_fin_to_dict(x) for x in items]})

@bp.post("/financial/payment-methods")
@jwt_required()
def paymethods_create():
    lab = _lab()
    data = request.get_json(force=True, silent=True) or {}
    obj = PaymentMethod(lab=lab,
                        code=data.get('code'),
                        name=data.get('name'),
                        active=data.get('active', True)).save()
    return jsonify({"payment_method": _simple_fin_to_dict(obj)}), 201

# --- Financial: Series ---
@bp.get("/financial/series")
@jwt_required()
def series_list():
    lab = _lab()
    # Permission: series.read
    try:
        uid = get_jwt_identity()
        user = User.objects.get(id=uid)
        err = ensure(user, lab, 'series', 'read')
        if err:
            return jsonify(err), 403
    except Exception:
        pass
    items = Series.objects(lab=lab).order_by("doc_type")
    return jsonify({"items": [_series_to_dict(x) for x in items]})

@bp.post("/financial/series")
@jwt_required()
def series_create():
    lab = _lab()
    # Permission: series.create
    try:
        uid = get_jwt_identity()
        user = User.objects.get(id=uid)
        err = ensure(user, lab, 'series', 'create')
        if err:
            return jsonify(err), 403
    except Exception:
        pass
    data = request.get_json(force=True, silent=True) or {}
    s = Series(lab=lab,
               doc_type=data.get('doc_type'),
               prefix=data.get('prefix') or '',
               next_number=int(data.get('next_number') or 1),
               padding=int(data.get('padding') or 5),
               active=bool(data.get('active') if data.get('active') is not None else True)).save()
    return jsonify({"series": _series_to_dict(s)}), 201

@bp.put("/financial/series/<sid>")
@jwt_required()
def series_update(sid):
    lab = _lab()
    data = request.get_json(force=True, silent=True) or {}
    # Permission: series.update
    try:
        uid = get_jwt_identity()
        user = User.objects.get(id=uid)
        err = ensure(user, lab, 'series', 'update')
        if err:
            return jsonify(err), 403
    except Exception:
        pass
    try:
        s = Series.objects.get(id=sid, lab=lab)
        # Prevent changing doc_type if series has been used (next_number > 1)
        if "doc_type" in data and data["doc_type"] != s.doc_type and (getattr(s, 'next_number', 1) or 1) > 1:
            return jsonify({"error": "doc_type locked for used series"}), 400
        for f in ["doc_type","prefix","next_number","padding","active"]:
            if f in data and data[f] is not None:
                if f in ("next_number","padding"):
                    try:
                        setattr(s, f, int(data[f]))
                    except Exception:
                        continue
                else:
                    setattr(s, f, data[f])
        s.save()
        return jsonify({"series": _series_to_dict(s)})
    except DoesNotExist:
        return jsonify({"error": ERR_NOT_FOUND}), 404
    except (ValidationError, Exception) as e:
        return jsonify({"error": str(e)}), 400

# --- Financial: SMTP Configuration ---
@bp.get("/financial/smtp")
@jwt_required()
def smtp_get():
    lab = _lab()
    # Permission: smtp.read
    try:
        uid = get_jwt_identity()
        user = User.objects.get(id=uid)
        err = ensure(user, lab, 'smtp', 'read')
        if err:
            return jsonify(err), 403
    except Exception:
        pass
    # Cleanup deprecated fields if present in the collection (one-time best-effort)
    try:
        col = SmtpConfig._get_collection()
        col.update_many({"lab": lab.id}, {"$unset": {"from_name": "", "from_email": ""}})
    except Exception:
        pass
    cfg = SmtpConfig.objects(lab=lab).first()
    return jsonify({"smtp": _smtp_to_dict(cfg)})

@bp.put("/financial/smtp")
@jwt_required()
def smtp_update():
    lab = _lab()
    # Permission: smtp.update
    try:
        uid = get_jwt_identity()
        user = User.objects.get(id=uid)
        err = ensure(user, lab, 'smtp', 'update')
        if err:
            return jsonify(err), 403
    except Exception:
        pass
    data = request.get_json(force=True, silent=True) or {}
    cfg = SmtpConfig.objects(lab=lab).first()
    if not cfg:
        cfg = SmtpConfig(lab=lab)
    # Update fields
    for f in ["server","use_tls","use_ssl","username"]:
        if f in data:
            setattr(cfg, f, data[f])
    # Port cast
    if "port" in data and data.get("port") is not None and data.get("port") != "":
        try:
            cfg.port = int(data.get("port"))
        except Exception:
            pass
    # Password: only update if provided and non-empty
    if "password" in data and (data.get("password") or "").strip():
        cfg.password = data.get("password")
    cfg.save()
    # Ensure deprecated fields are removed from DB
    try:
        SmtpConfig._get_collection().update_one({"_id": cfg.id}, {"$unset": {"from_name": "", "from_email": ""}})
    except Exception:
        pass
    return jsonify({"smtp": _smtp_to_dict(cfg)})

@bp.post("/financial/smtp/test")
@jwt_required()
def smtp_test():
    """Testa conectividade SMTP. Se receber um parâmetro 'to', envia um email de teste.

    Payload opcional:
      - to: endereço para envio de email de teste (opcional)
      - subject/body: campos opcionais para personalizar o email de teste
    """
    lab = _lab()
    data = request.get_json(force=True, silent=True) or {}
    to = (data.get("to") or "").strip()
    subject = (data.get("subject") or "SMTP Test").strip()
    body = (data.get("body") or "Este é um email de teste do Vivae Dental ERP.").strip()

    cfg = SmtpConfig.objects(lab=lab).first()
    if not cfg or not cfg.server:
        # padrão de erro compatível
        return jsonify({"error": "smtp not configured"}), 400

    def _connect(use_ssl: bool, use_tls: bool, port: int | None):
        srv = None
        if use_ssl:
            srv = smtplib.SMTP_SSL(cfg.server, port or 465, timeout=15)
        else:
            srv = smtplib.SMTP(cfg.server, port or 587, timeout=15)
        srv.ehlo()
        if use_tls and not use_ssl:
            srv.starttls()
            srv.ehlo()
        if cfg.username:
            srv.login(cfg.username, cfg.password or '')
        return srv

    # Se não há destinatário, apenas testa a conectividade com a configuração atual
    if not to:
        try:
            srv = _connect(bool(getattr(cfg, 'use_ssl', False)), bool(getattr(cfg, 'use_tls', False)), getattr(cfg, 'port', None))
            try:
                srv.quit()
            except Exception:
                pass
            return jsonify({"ok": True})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500

    # Envio de email de teste: tenta configuração atual e alternativas comuns
    msg = EmailMessage()
    sender = cfg.username or ""
    msg["Subject"] = subject or "SMTP Test"
    msg["From"] = sender
    msg["To"] = to
    msg.set_content(body or "Este é um email de teste do Vivae Dental ERP.")

    tried: list[tuple[bool, bool, int | None]] = []
    def add_combo(u_ssl, u_tls, prt):
        key = (bool(u_ssl), bool(u_tls), int(prt) if prt else None)
        if key not in tried:
            tried.append(key)

    # atual
    add_combo(getattr(cfg, 'use_ssl', False), getattr(cfg, 'use_tls', False), getattr(cfg, 'port', None))
    # alternativas comuns
    add_combo(True, False, 465)
    add_combo(False, True, 587)
    add_combo(False, False, 25)

    errors = []
    for u_ssl, u_tls, prt in tried:
        srv = None
        try:
            srv = _connect(u_ssl, u_tls, prt)
            srv.send_message(msg)
            try:
                srv.quit()
            except Exception:
                pass
            # sucesso
            if (u_ssl, u_tls, prt) != (bool(getattr(cfg, 'use_ssl', False)), bool(getattr(cfg, 'use_tls', False)), getattr(cfg, 'port', None)):
                used_port = prt or (465 if u_ssl else 587)
                return jsonify({"ok": True, "fallback": {"use_ssl": bool(u_ssl), "use_tls": bool(u_tls), "port": int(used_port)}})
            return jsonify({"ok": True})
        except Exception as ex:
            errors.append(f"ssl={u_ssl} tls={u_tls} port={prt or (465 if u_ssl else 587)} -> {ex.__class__.__name__}: {str(ex)}")
        finally:
            try:
                if srv:
                    srv.quit()
            except Exception:
                pass

    return jsonify({"error": "; ".join(errors) or "unknown smtp error"}), 500

@bp.post("/financial/smtp/diagnose")
@jwt_required()
def smtp_diagnose():
    """Diagnóstico detalhado SMTP: resolve DNS, testa conectividade a portas comuns,
    verifica EHLO/STARTTLS e AUTH, e tenta login (sem enviar email).

    Retorna um relatório estruturado útil para comparar DEV vs PRODUÇÃO.
    """
    lab = _lab()
    cfg = SmtpConfig.objects(lab=lab).first()
    if not cfg or not cfg.server:
        return jsonify({"error": "smtp not configured"}), 400

    host = cfg.server
    result: dict = {
        "host": host,
        "env": {
            "render": (current_app.config.get('RENDER') or (os.getenv('RENDER') == 'true')) if 'os' in globals() else (os.getenv('RENDER') == 'true'),
            "env": (os.getenv('ENV') or os.getenv('FLASK_ENV')) if 'os' in globals() else None,
        }
    }

    # DNS resolution
    try:
        infos = socket.getaddrinfo(host, None)
        addrs = []
        for fam, _, _, _, sockaddr in infos:
            try:
                fam_name = 'AF_INET6' if fam == socket.AF_INET6 else 'AF_INET' if fam == socket.AF_INET else str(fam)
            except Exception:
                fam_name = str(fam)
            ip = sockaddr[0] if isinstance(sockaddr, tuple) and len(sockaddr) else str(sockaddr)
            if ip not in [a.get('ip') for a in addrs]:
                addrs.append({"family": fam_name, "ip": ip})
        result["resolve"] = {"ok": True, "addresses": addrs}
    except Exception as e:
        result["resolve"] = {"ok": False, "error": f"{e.__class__.__name__}: {e}"}

    # Port matrix
    ports = []
    def add_port(p):
        if p and int(p) not in ports:
            ports.append(int(p))
    add_port(getattr(cfg, 'port', None))
    for p in (465, 587, 25):
        add_port(p)

    tests = []
    for p in ports:
        entry = {"port": p, "ssl": (p == 465), "tls": (p == 587 and bool(getattr(cfg, 'use_tls', True))) }
        # socket connectivity
        try:
            s = socket.create_connection((host, p), timeout=10)
            s.close()
            entry["connect_ok"] = True
        except Exception as e:
            entry["connect_ok"] = False
            entry["connect_error"] = f"{e.__class__.__name__}: {e}"
            tests.append(entry)
            continue
        # SMTP handshake
        srv = None
        banner = None
        ehlo_ok = False
        features = {}
        starttls_ok = None
        auth_mechs = []
        login_ok = None
        login_error = None
        try:
            if p == 465 or bool(getattr(cfg, 'use_ssl', False)):
                srv = smtplib.SMTP_SSL(host, p, timeout=25)
            else:
                srv = smtplib.SMTP(host, p, timeout=25)
            try:
                code, msg = srv.noop()
                banner = f"NOOP {code}"
            except Exception:
                pass
            try:
                srv.ehlo()
                ehlo_ok = True
                try:
                    features = dict(getattr(srv, 'esmtp_features', {}) or {})
                except Exception:
                    features = {}
            except Exception:
                ehlo_ok = False
            # STARTTLS if supported and not already SSL
            if not isinstance(srv, smtplib.SMTP_SSL):
                if 'starttls' in {k.lower(): v for k, v in (features or {}).items()}:
                    try:
                        srv.starttls()
                        srv.ehlo()
                        starttls_ok = True
                        try:
                            features = dict(getattr(srv, 'esmtp_features', {}) or {})
                        except Exception:
                            pass
                    except Exception as e:
                        starttls_ok = False
                        entry["starttls_error"] = f"{e.__class__.__name__}: {e}"
            # AUTH mechs
            try:
                caps = {k.lower(): v for k, v in (features or {}).items()}
                if 'auth' in caps:
                    auth_mechs = caps['auth'].split()
            except Exception:
                auth_mechs = []
            # Try login if username
            if cfg.username:
                try:
                    srv.login(cfg.username, cfg.password or '')
                    login_ok = True
                except Exception as le:
                    login_ok = False
                    login_error = f"{le.__class__.__name__}: {le}"
        except Exception as e:
            entry["error"] = f"{e.__class__.__name__}: {e}"
        finally:
            try:
                if srv:
                    srv.quit()
            except Exception:
                pass
        entry.update({
            "banner": banner,
            "ehlo_ok": ehlo_ok,
            "features": features,
            "starttls_ok": starttls_ok,
            "auth_mechs": auth_mechs,
            "login_ok": login_ok,
        })
        if login_error:
            entry["login_error"] = login_error
        tests.append(entry)

    result["tests"] = tests
    return jsonify(result)

# --- Countries ---
def _country_to_dict(o: Country):
    return {"id": str(o.id), "code": o.code, "name": o.name}

@bp.get("/countries")
@jwt_required()
def countries_list():
    items = Country.objects.order_by("name")
    return jsonify({"items": [_country_to_dict(x) for x in items]})

@bp.post("/countries")
@jwt_required()
def countries_create():
    data = request.get_json(force=True, silent=True) or {}
    try:
        c = Country(code=(data.get("code") or "").upper(), name=data.get("name"))
        c.save()
        return jsonify({"country": _country_to_dict(c)}), 201
    except (ValidationError, Exception) as e:
        return jsonify({"error": str(e)}), 400

@bp.put("/countries/<cid>")
@jwt_required()
def countries_update(cid):
    data = request.get_json(force=True, silent=True) or {}
    try:
        c = Country.objects.get(id=cid)
        # Unique code check if changing
        if 'code' in data and data['code']:
            new_code = (data.get('code') or '').upper()
            # If code is changing, prevent change when referenced
            if new_code != c.code:
                ref_sa = ShippingAddress.objects(country_code=c.code).count()
                ref_cli = Client.objects(country_code=c.code).count()
                if (ref_sa or ref_cli):
                    return jsonify({
                        "error": "country code in use",
                        "field": "code",
                        "references": {"shipping_addresses": int(ref_sa), "clients": int(ref_cli)}
                    }), 400
            dup = Country.objects(code=new_code, id__ne=c.id).first()
            if dup:
                return jsonify({"error": "country exists", "field": "code"}), 409
            c.code = new_code
        if 'name' in data:
            c.name = data.get('name')
        c.save()
        return jsonify({"country": _country_to_dict(c)})
    except DoesNotExist:
        return jsonify({"error": ERR_NOT_FOUND}), 404
    except (ValidationError, Exception) as e:
        return jsonify({"error": str(e)}), 400

@bp.delete("/countries/<cid>")
@jwt_required()
def countries_delete(cid):
    try:
        c = Country.objects.get(id=cid)
        # Prevent deleting if referenced by ShippingAddress or Client
        ref_sa = ShippingAddress.objects(country_code=c.code).count()
        ref_cli = Client.objects(country_code=c.code).count()
        if (ref_sa or ref_cli):
            return jsonify({
                "error": "country in use",
                "references": {"shipping_addresses": int(ref_sa), "clients": int(ref_cli)}
            }), 400
        c.delete()
        return jsonify({"status": "deleted"})
    except DoesNotExist:
        return jsonify({"error": ERR_NOT_FOUND}), 404

# --- Shipping Addresses ---
def _shipaddr_to_dict(a: ShippingAddress):
    return {
        "id": str(a.id),
        "lab_id": str(getattr(a.lab, 'id', '')),
        "client_id": str(getattr(a.client, 'id', '')) if getattr(a, 'client', None) else None,
        "code": a.code,
        "address1": a.address1 or "",
        "address2": a.address2 or "",
        "postal_code": a.postal_code or "",
        "city": a.city or "",
        "country_code": a.country_code or "",
    }

def _clientprice_to_dict(p: ClientPrice):
    return {
        "id": str(p.id),
        "lab_id": str(getattr(p.lab, 'id', '')),
        "client_id": str(getattr(p.client, 'id', '')) if getattr(p, 'client', None) else None,
        "sale_type": p.sale_type or "",
        "sale_code": p.sale_code or "",
        "code": p.code or "",
        "uom": p.uom or "",
        "min_qty": int(getattr(p, 'min_qty', 1) or 1),
        "unit_price": float(getattr(p, 'unit_price', 0) or 0),
        "start_date": _date_to_iso(getattr(p, 'start_date', None)),
        "end_date": _date_to_iso(getattr(p, 'end_date', None)),
    }

@bp.get("/clients/<cid>/resolve-price")
@jwt_required()
def client_resolve_price(cid):
    """Resolve client-specific unit price for a sale item.

    Query params:
      - sale_type: 'service' | 'product' (optional for now, defaults to any)
      - code: item code to match (required)
      - qty: numeric quantity (default 1)
      - date: 'YYYY-MM-DD' (optional, defaults to today)
    Returns: { unit_price: number | null }
    """
    lab = _lab()
    try:
        cli = Client.objects.get(id=cid, lab=lab)
    except DoesNotExist:
        return jsonify({"error": ERROR_CLIENT_NOT_FOUND}), 404
    sale_type = (request.args.get('sale_type') or '').strip().lower()
    code = (request.args.get('code') or '').strip()
    try:
        qty = float(request.args.get('qty') or 1)
    except Exception:
        qty = 1.0
    d = _parse_date(request.args.get('date') or date.today().isoformat())
    if not code:
        return jsonify({"unit_price": None})
    # Query candidate prices
    qs = ClientPrice.objects(lab=lab, client=cli, code=code)
    if sale_type:
        qs = qs.filter(sale_type=sale_type)
    cands = list(qs)
    # Filter by qty and date window
    def in_window(p: ClientPrice) -> bool:
        if getattr(p, 'min_qty', None) and qty < float(getattr(p, 'min_qty') or 0):
            return False
        sd = getattr(p, 'start_date', None)
        ed = getattr(p, 'end_date', None)
        if sd and d and d < sd:
            return False
        if ed and d and d > ed:
            return False
        return True
    cands = [p for p in cands if in_window(p)]
    if not cands:
        return jsonify({"unit_price": None})
    # Sort by highest min_qty, then latest start_date
    def sort_key(p: ClientPrice):
        mq = int(getattr(p, 'min_qty', 0) or 0)
        sd = getattr(p, 'start_date', None)
        sdv = int(sd.toordinal()) if sd else 0
        return (-mq, -sdv)
    cands.sort(key=sort_key)
    up = float(getattr(cands[0], 'unit_price', 0) or 0)
    return jsonify({"unit_price": up})

@bp.get("/shipping-addresses")
@jwt_required()
def shipaddrs_list():
    lab = _lab()
    client_id = (request.args.get('client') or '').strip()
    qs = ShippingAddress.objects(lab=lab)
    if client_id:
        try:
            cli = Client.objects.get(id=client_id, lab=lab)
            qs = qs.filter(client=cli)
        except Exception:
            qs = qs.filter(id=None)  # empty
    items = qs.order_by("code")
    return jsonify({"items": [_shipaddr_to_dict(x) for x in items]})

@bp.post("/shipping-addresses")
@jwt_required()
def shipaddrs_create():
    lab = _lab()
    data = request.get_json(force=True, silent=True) or {}
    try:
        # resolve client (required for new addresses)
        cli = None
        cli_id = (data.get('client') or '').strip()
        if cli_id:
            try:
                cli = Client.objects.get(id=cli_id, lab=lab)
            except Exception:
                return jsonify({"error": ERROR_CLIENT_NOT_FOUND, "field": "client"}), 400
        # unique code per lab
        if ShippingAddress.objects(lab=lab, client=cli, code=data.get('code')).first():
            return jsonify({"error": ERROR_ADDRESS_EXISTS, "field": "code"}), 409
        # validate country_code exists if provided
        cc = (data.get('country_code') or '').upper() or None
        if cc:
            if not Country.objects(code=cc).first():
                return jsonify({"error": ERR_INVALID_COUNTRY_CODE, "field": "country_code"}), 400
        a = ShippingAddress(
            lab=lab,
            client=cli,
            code=data.get('code'),
            address1=data.get('address1'),
            address2=data.get('address2'),
            postal_code=data.get('postal_code'),
            city=data.get('city'),
            country_code=cc,
        ).save()
        return jsonify({"shipping_address": _shipaddr_to_dict(a)}), 201
    except (ValidationError, Exception) as e:
        return jsonify({"error": str(e)}), 400

@bp.put("/shipping-addresses/<aid>")
@jwt_required()
def shipaddrs_update(aid):
    lab = _lab()
    data = request.get_json(force=True, silent=True) or {}
    try:
        a = ShippingAddress.objects.get(id=aid, lab=lab)
        # Optional client reassignment (rare): if client provided, revalidate uniqueness per (lab, client, code)
        if 'client' in data:
            cli = None
            cli_id = (data.get('client') or '').strip()
            if cli_id:
                try:
                    cli = Client.objects.get(id=cli_id, lab=lab)
                except Exception:
                    return jsonify({"error": ERROR_CLIENT_NOT_FOUND, "field": "client"}), 400
            a.client = cli
        if 'code' in data:
            new_code = data.get('code')
            dup = ShippingAddress.objects(lab=lab, client=getattr(a,'client',None), code=new_code, id__ne=a.id).first()
            if dup:
                return jsonify({"error": ERROR_ADDRESS_EXISTS, "field": "code"}), 409
        # Normalize and validate country_code if present
        if 'country_code' in data:
            cc = (data.get('country_code') or '').upper() or None
            if cc and not Country.objects(code=cc).first():
                return jsonify({"error": ERR_INVALID_COUNTRY_CODE, "field": "country_code"}), 400
            data['country_code'] = cc
        for f in ['code','address1','address2','postal_code','city','country_code']:
            if f in data:
                setattr(a, f, data.get(f))
        a.save()
        return jsonify({"shipping_address": _shipaddr_to_dict(a)})
    except DoesNotExist:
        return jsonify({"error": ERR_NOT_FOUND}), 404
    except (ValidationError, Exception) as e:
        return jsonify({"error": str(e)}), 400

@bp.delete("/shipping-addresses/<aid>")
@jwt_required()
def shipaddrs_delete(aid):
    lab = _lab()
    try:
        a = ShippingAddress.objects.get(id=aid, lab=lab)
        # If any client has this code as default, clear it
        try:
            if getattr(a, 'client', None):
                Client.objects(lab=lab, id=a.client.id, default_shipping_address=a.code).update(unset__default_shipping_address=1)
            else:
                # legacy: clear anyone using this code (rare)
                Client.objects(lab=lab, default_shipping_address=a.code).update(unset__default_shipping_address=1)
        except Exception:
            pass
        a.delete()
        return jsonify({"status": "deleted"})
    except DoesNotExist:
        return jsonify({"error": ERR_NOT_FOUND}), 404

# Nested shipping addresses under a specific client
@bp.get("/clients/<cid>/shipping-addresses")
@jwt_required()
def client_shipaddrs_list(cid):
    lab = _lab()
    try:
        cli = Client.objects.get(id=cid, lab=lab)
    except DoesNotExist:
        return jsonify({"error": ERROR_CLIENT_NOT_FOUND}), 404
    items = ShippingAddress.objects(lab=lab, client=cli).order_by("code")
    return jsonify({"items": [_shipaddr_to_dict(x) for x in items]})

@bp.post("/clients/<cid>/shipping-addresses")
@jwt_required()
def client_shipaddrs_create(cid):
    lab = _lab()
    data = request.get_json(force=True, silent=True) or {}
    try:
        cli = Client.objects.get(id=cid, lab=lab)
    except DoesNotExist:
        return jsonify({"error": ERROR_CLIENT_NOT_FOUND}), 404
    try:
        # unique code per client
        if ShippingAddress.objects(lab=lab, client=cli, code=data.get('code')).first():
            return jsonify({"error": ERROR_ADDRESS_EXISTS, "field": "code"}), 409
        cc = (data.get('country_code') or '').upper() or None
        if cc and not Country.objects(code=cc).first():
            return jsonify({"error": ERR_INVALID_COUNTRY_CODE, "field": "country_code"}), 400
        a = ShippingAddress(
            lab=lab,
            client=cli,
            code=data.get('code'),
            address1=data.get('address1'),
            address2=data.get('address2'),
            postal_code=data.get('postal_code'),
            city=data.get('city'),
            country_code=cc,
        ).save()
        return jsonify({"shipping_address": _shipaddr_to_dict(a)}), 201
    except (ValidationError, Exception) as e:
        return jsonify({"error": str(e)}), 400

@bp.put("/clients/<cid>/shipping-addresses/<aid>")
@jwt_required()
def client_shipaddrs_update(cid, aid):
    lab = _lab()
    try:
        cli = Client.objects.get(id=cid, lab=lab)
    except DoesNotExist:
        return jsonify({"error": ERROR_CLIENT_NOT_FOUND}), 404
    data = request.get_json(force=True, silent=True) or {}
    try:
        a = ShippingAddress.objects.get(id=aid, lab=lab, client=cli)
        if 'code' in data:
            new_code = data.get('code')
            dup = ShippingAddress.objects(lab=lab, client=cli, code=new_code, id__ne=a.id).first()
            if dup:
                return jsonify({"error": ERROR_ADDRESS_EXISTS, "field": "code"}), 409
        if 'country_code' in data:
            cc = (data.get('country_code') or '').upper() or None
            if cc and not Country.objects(code=cc).first():
                return jsonify({"error": ERR_INVALID_COUNTRY_CODE, "field": "country_code"}), 400
            data['country_code'] = cc
        for f in ['code','address1','address2','postal_code','city','country_code']:
            if f in data:
                setattr(a, f, data.get(f))
        a.save()
        return jsonify({"shipping_address": _shipaddr_to_dict(a)})
    except DoesNotExist:
        return jsonify({"error": ERR_NOT_FOUND}), 404
    except (ValidationError, Exception) as e:
        return jsonify({"error": str(e)}), 400

@bp.delete("/clients/<cid>/shipping-addresses/<aid>")
@jwt_required()
def client_shipaddrs_delete(cid, aid):
    lab = _lab()
    try:
        cli = Client.objects.get(id=cid, lab=lab)
    except DoesNotExist:
        return jsonify({"error": ERROR_CLIENT_NOT_FOUND}), 404
    try:
        a = ShippingAddress.objects.get(id=aid, lab=lab, client=cli)
        # Clear client's default if this code was default
        try:
            Client.objects(id=cli.id, lab=lab, default_shipping_address=a.code).update(unset__default_shipping_address=1)
        except Exception:
            pass
        a.delete()
        return jsonify({"status": "deleted"})
    except DoesNotExist:
        return jsonify({"error": ERR_NOT_FOUND}), 404

# --- Client Prices (nested under client) ---
@bp.get("/clients/<cid>/prices")
@jwt_required()
def client_prices_list(cid):
    lab = _lab()
    try:
        cli = Client.objects.get(id=cid, lab=lab)
    except DoesNotExist:
        return jsonify({"error": ERROR_CLIENT_NOT_FOUND}), 404
    items = ClientPrice.objects(lab=lab, client=cli).order_by("code")
    return jsonify({"items": [_clientprice_to_dict(x) for x in items]})

@bp.post("/clients/<cid>/prices")
@jwt_required()
def client_prices_create(cid):
    lab = _lab()
    data = request.get_json(force=True, silent=True) or {}
    try:
        cli = Client.objects.get(id=cid, lab=lab)
    except DoesNotExist:
        return jsonify({"error": ERROR_CLIENT_NOT_FOUND}), 404
    try:
        cp = ClientPrice(
            lab=lab,
            client=cli,
            sale_type=data.get('sale_type'),
            sale_code=data.get('sale_code'),
            code=data.get('code'),
            uom=data.get('uom'),
            min_qty=int(data.get('min_qty') or 1),
            unit_price=float(data.get('unit_price') or 0),
            start_date=_parse_date(data.get('start_date')),
            end_date=_parse_date(data.get('end_date')),
        ).save()
        return jsonify({"price": _clientprice_to_dict(cp)}), 201
    except (ValidationError, Exception) as e:
        return jsonify({"error": str(e)}), 400

@bp.put("/clients/<cid>/prices/<pid>")
@jwt_required()
def client_prices_update(cid, pid):
    lab = _lab()
    data = request.get_json(force=True, silent=True) or {}
    try:
        cli = Client.objects.get(id=cid, lab=lab)
    except DoesNotExist:
        return jsonify({"error": ERROR_CLIENT_NOT_FOUND}), 404
    try:
        cp = ClientPrice.objects.get(id=pid, lab=lab, client=cli)
        for f in ['sale_type','sale_code','code','uom']:
            if f in data:
                setattr(cp, f, data.get(f))
        if 'min_qty' in data:
            try:
                cp.min_qty = int(data.get('min_qty') or 1)
            except Exception:
                pass
        if 'unit_price' in data:
            try:
                cp.unit_price = float(data.get('unit_price') or 0)
            except Exception:
                pass
        if 'start_date' in data:
            cp.start_date = _parse_date(data.get('start_date'))
        if 'end_date' in data:
            cp.end_date = _parse_date(data.get('end_date'))
        cp.save()
        return jsonify({"price": _clientprice_to_dict(cp)})
    except DoesNotExist:
        return jsonify({"error": ERR_NOT_FOUND}), 404
    except (ValidationError, Exception) as e:
        return jsonify({"error": str(e)}), 400

@bp.delete("/clients/<cid>/prices/<pid>")
@jwt_required()
def client_prices_delete(cid, pid):
    lab = _lab()
    try:
        cli = Client.objects.get(id=cid, lab=lab)
    except DoesNotExist:
        return jsonify({"error": ERROR_CLIENT_NOT_FOUND}), 404
    try:
        cp = ClientPrice.objects.get(id=pid, lab=lab, client=cli)
        cp.delete()
        return jsonify({"status": "deleted"})
    except DoesNotExist:
        return jsonify({"error": ERR_NOT_FOUND}), 404

