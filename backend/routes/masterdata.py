# backend/routes/masterdata.py
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt
from mongoengine.errors import ValidationError, DoesNotExist
from mongoengine.queryset.visitor import Q
from typing import Tuple
from datetime import date

from models.laboratory import Laboratory
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
from models.smtp_config import SmtpConfig
import smtplib
from email.message import EmailMessage
import smtplib

bp = Blueprint("masterdata", __name__, url_prefix="/api/masterdata")

# --- Helpers ---

def _pagination() -> Tuple[int, int]:
    page = max(1, int(request.args.get("page", 1) or 1))
    size = min(100, max(1, int(request.args.get("page_size", 20) or 20)))
    return page, size

def _q() -> str:
    return (request.args.get("q", "") or "").strip()


def _lab() -> Laboratory:
    """Resolve lab a partir do JWT (tenant_id) ou fallback p/ primeiro laboratório."""
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
        today = date.today()
        years = today.year - dt.year - ((today.month, today.day) < (dt.month, dt.day))
        return years
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
        "birthdate": p.birthdate.isoformat() if getattr(p, "birthdate", None) else None,
        "age": _age_from_birthdate(getattr(p, "birthdate", None)),
        "email": p.email or "",
        "phone": p.phone or "",
        "address": getattr(p, "address", "") or "",
        "notes": p.notes or "",
        "created_at": getattr(p, "created_at", None).isoformat() if getattr(p, "created_at", None) else None,
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
        "birthdate": c.birthdate.isoformat() if getattr(c, "birthdate", None) else None,
        "age": _age_from_birthdate(getattr(c, "birthdate", None)),
        "email": c.email or "",
        "phone": c.phone or "",
        "address": getattr(c, "address", "") or "",
        "type": c.type or "",
        "tax_id": c.tax_id or "",
        "billing_address": c.billing_address or {},
        "shipping_address": c.shipping_address or {},
        "payment_terms": c.payment_terms or "",
        "notes": c.notes or "",
        "active": bool(getattr(c, "active", True)),
        "contacts": c.contacts or [],
        "created_at": getattr(c, "created_at", None).isoformat() if getattr(c, "created_at", None) else None,
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
    labs = Laboratory.objects.order_by("name")
    return jsonify({"laboratories": [_lab_to_dict(x) for x in labs]})

@bp.post("/laboratories")
@jwt_required()
def labs_create():
    data = request.get_json(force=True, silent=True) or {}
    try:
        lab = Laboratory(
            name=data.get("name"),
            address=data.get("address"),
            country=data.get("country"),
            postal_code=data.get("postal_code"),
            city=data.get("city"),
            tax_id=data.get("tax_id"),
            phone=data.get("phone"),
            email=data.get("email"),
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
        lab = Laboratory.objects.get(id=lab_id)
        for f in ["name","address","country","postal_code","city","tax_id","phone","email","active"]:
            if f in data: setattr(lab, f, data[f])
        lab.save()
        return jsonify({"laboratory": _lab_to_dict(lab)})
    except DoesNotExist:
        return jsonify({"error": "not found"}), 404
    except (ValidationError, Exception) as e:
        return jsonify({"error": str(e)}), 400

# --- Patients ---
@bp.get("/patients")
@jwt_required()
def patients_list():
    lab = _lab()
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
    data = request.get_json(force=True, silent=True) or {}
    try:
        p = Patient(
            lab=lab,
            name=data.get("name") or (f"{data.get('first_name','').strip()} {data.get('last_name','').strip()}".strip() or None),
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            gender=data.get("gender"),
            birthdate=data.get("birthdate"),
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
    try:
        p = Patient.objects.get(id=pid, lab=lab)
        for f in ["name","first_name","last_name","gender","birthdate","email","phone","address","notes"]:
            if f in data: setattr(p, f, data[f])
        # Atualiza name se não for fornecido mas first/last mudaram
        if not data.get("name") and ("first_name" in data or "last_name" in data):
            full = f"{getattr(p,'first_name','') or ''} {getattr(p,'last_name','') or ''}".strip()
            if full:
                p.name = full
        p.save()
        return jsonify({"patient": _patient_to_dict(p)})
    except DoesNotExist:
        return jsonify({"error": "not found"}), 404
    except (ValidationError, Exception) as e:
        return jsonify({"error": str(e)}), 400

@bp.delete("/patients/<pid>")
@jwt_required()
def patients_delete(pid):
    lab = _lab()
    try:
        p = Patient.objects.get(id=pid, lab=lab)
        p.delete()
        return jsonify({"status": "deleted"})
    except DoesNotExist:
        return jsonify({"error": "not found"}), 404

# --- Technicians ---
@bp.get("/technicians")
@jwt_required()
def techs_list():
    lab = _lab()
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
    try:
        t = Technician.objects.get(id=tid, lab=lab)
        for f in ["name","email","phone","workcenter"]:
            if f in data: setattr(t, f, data[f])
        t.save()
        return jsonify({"technician": _technician_to_dict(t)})
    except DoesNotExist:
        return jsonify({"error": "not found"}), 404
    except (ValidationError, Exception) as e:
        return jsonify({"error": str(e)}), 400

@bp.delete("/technicians/<tid>")
@jwt_required()
def techs_delete(tid):
    lab = _lab()
    try:
        t = Technician.objects.get(id=tid, lab=lab)
        t.delete()
        return jsonify({"status": "deleted"})
    except DoesNotExist:
        return jsonify({"error": "not found"}), 404

# --- Services ---
@bp.get("/services")
@jwt_required()
def services_list():
    lab = _lab()
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
    try:
        s = Service.objects.get(id=sid, lab=lab)
        for f in ["name","code","price","description"]:
            if f in data: setattr(s, f, data[f])
        s.save()
        return jsonify({"service": _service_to_dict(s)})
    except DoesNotExist:
        return jsonify({"error": "not found"}), 404
    except (ValidationError, Exception) as e:
        return jsonify({"error": str(e)}), 400

@bp.delete("/services/<sid>")
@jwt_required()
def services_delete(sid):
    lab = _lab()
    try:
        s = Service.objects.get(id=sid, lab=lab)
        s.delete()
        return jsonify({"status": "deleted"})
    except DoesNotExist:
        return jsonify({"error": "not found"}), 404

# --- Document Types ---
@bp.get("/document-types")
@jwt_required()
def doctypes_list():
    lab = _lab()
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
    try:
        d = DocumentType.objects.get(id=did, lab=lab)
        for f in ["name","extension"]:
            if f in data: setattr(d, f, data[f])
        d.save()
        return jsonify({"document_type": _doctype_to_dict(d)})
    except DoesNotExist:
        return jsonify({"error": "not found"}), 404
    except (ValidationError, Exception) as e:
        return jsonify({"error": str(e)}), 400

@bp.delete("/document-types/<did>")
@jwt_required()
def doctypes_delete(did):
    lab = _lab()
    try:
        d = DocumentType.objects.get(id=did, lab=lab)
        d.delete()
        return jsonify({"status": "deleted"})
    except DoesNotExist:
        return jsonify({"error": "not found"}), 404

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
            return jsonify({"error": "client exists", "field": "code"}), 409
        if tax_id and Client.objects(lab=lab, tax_id=tax_id).first():
            return jsonify({"error": "client exists", "field": "tax_id"}), 409
        if email and Client.objects(lab=lab, email=email).first():
            return jsonify({"error": "client exists", "field": "email"}), 409

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

        c = Client(
            lab=lab,
            code=code,
            name=data.get("name") or (f"{data.get('first_name','').strip()} {data.get('last_name','').strip()}".strip() or None),
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            gender=data.get("gender"),
            birthdate=data.get("birthdate"),
            email=email,
            phone=data.get("phone"),
            address=data.get("address"),
            type=data.get("type"),
            tax_id=tax_id,
            billing_address=data.get("billing_address"),
            shipping_address=data.get("shipping_address"),
            payment_terms=data.get("payment_terms"),
            notes=data.get("notes"),
            active=data.get("active", True),
            contacts=data.get("contacts") or [],
            preferred_currency=pc,
            payment_type=pt,
            payment_form=pf,
            payment_method=pm,
        ).save()
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
                return jsonify({"error": "client exists", "field": "code"}), 409
        tax_id = (data.get("tax_id") if "tax_id" in data else c.tax_id) or None
        email = (data.get("email") if "email" in data else c.email) or None
        # Duplicate check excluding current
        if tax_id:
            dup = Client.objects(lab=lab, tax_id=tax_id, id__ne=c.id).first()
            if dup:
                return jsonify({"error": "client exists", "field": "tax_id"}), 409
        if email:
            dup = Client.objects(lab=lab, email=email, id__ne=c.id).first()
            if dup:
                return jsonify({"error": "client exists", "field": "email"}), 409

        for f in [
            "code","name","first_name","last_name","gender","birthdate","email","phone","address",
            "type","tax_id","billing_address","shipping_address","payment_terms","notes","active","contacts"
        ]:
            if f in data: setattr(c, f, data[f])
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
        return jsonify({"error": "not found"}), 404
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
        return jsonify({"error": "not found"}), 404

# Single client
@bp.get("/clients/<cid>")
@jwt_required()
def clients_get(cid):
    lab = _lab()
    try:
        c = Client.objects.get(id=cid, lab=lab)
        return jsonify({"client": _client_to_dict(c)})
    except DoesNotExist:
        return jsonify({"error": "not found"}), 404

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
    items = Series.objects(lab=lab).order_by("doc_type")
    return jsonify({"items": [_series_to_dict(x) for x in items]})

@bp.post("/financial/series")
@jwt_required()
def series_create():
    lab = _lab()
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
        return jsonify({"error": "not found"}), 404
    except (ValidationError, Exception) as e:
        return jsonify({"error": str(e)}), 400

# --- Financial: SMTP Configuration ---
@bp.get("/financial/smtp")
@jwt_required()
def smtp_get():
    lab = _lab()
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
    lab = _lab()
    data = request.get_json(force=True, silent=True) or {}
    to = (data.get("to") or "").strip()
    cfg = SmtpConfig.objects(lab=lab).first()
    if not cfg or not cfg.server:
        return jsonify({"error": "smtp not configured"}), 400
    if not to:
        return jsonify({"error": "missing 'to'"}), 400
    # Build simple test email
    msg = EmailMessage()
    sender = cfg.username or ""
    msg["Subject"] = "SMTP Test"
    msg["From"] = sender
    msg["To"] = to
    msg.set_content("Este é um email de teste do Vivae Dental ERP.")
    def _try_send(use_ssl: bool, use_tls: bool, port: int | None):
        srv = None
        try:
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
            srv.send_message(msg)
            return True, None
        except Exception as ex:
            return False, f"{ex.__class__.__name__}: {str(ex)}"
        finally:
            try:
                if srv:
                    srv.quit()
            except Exception:
                pass

    tried = []
    def add_combo(u_ssl, u_tls, prt):
        key = (bool(u_ssl), bool(u_tls), int(prt) if prt else None)
        if key not in tried:
            tried.append(key)

    # Try current config first
    add_combo(getattr(cfg, 'use_ssl', False), getattr(cfg, 'use_tls', False), getattr(cfg, 'port', None))
    # Common alternatives
    add_combo(True, False, 465)     # SSL 465
    add_combo(False, True, 587)     # STARTTLS 587
    add_combo(False, False, 25)     # Plain 25 (alguns provedores)

    errors = []
    for u_ssl, u_tls, prt in tried:
        ok, err = _try_send(u_ssl, u_tls, prt)
        if ok:
            # if differs from stored config, report fallback combo
            if (u_ssl, u_tls, prt) != (bool(getattr(cfg, 'use_ssl', False)), bool(getattr(cfg, 'use_tls', False)), getattr(cfg, 'port', None)):
                used_port = prt or (465 if u_ssl else 587)
                return jsonify({"ok": True, "fallback": {"use_ssl": bool(u_ssl), "use_tls": bool(u_tls), "port": int(used_port)}})
            return jsonify({"ok": True})
        else:
            errors.append(f"ssl={u_ssl} tls={u_tls} port={prt or (465 if u_ssl else 587)} -> {err}")

    return jsonify({"error": "; ".join(errors) or "unknown smtp error"}), 500

@bp.post("/financial/smtp/test")
@jwt_required()
def smtp_test():
    """Test SMTP connectivity and optional login using current settings."""
    lab = _lab()
    cfg = SmtpConfig.objects(lab=lab).first()
    if not cfg or not cfg.server:
        return jsonify({"ok": False, "error": "smtp not configured"}), 400
    try:
        if cfg.use_ssl:
            server = smtplib.SMTP_SSL(cfg.server, cfg.port or 465, timeout=10)
        else:
            server = smtplib.SMTP(cfg.server, cfg.port or 587, timeout=10)
        server.ehlo()
        if cfg.use_tls and not cfg.use_ssl:
            server.starttls()
        if cfg.username:
            server.login(cfg.username, cfg.password or '')
        server.quit()
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
