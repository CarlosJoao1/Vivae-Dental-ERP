from flask import Blueprint, request, jsonify, make_response, send_file
from flask_jwt_extended import jwt_required, get_jwt
from datetime import date, datetime
from models.laboratory import Laboratory
from models.order import Order
from models.invoice import Invoice
from models.series import Series
from models.currency import Currency
from models.payment_type import PaymentType
from models.payment_form import PaymentForm
from models.payment_method import PaymentMethod
from models.client import Client
from models.smtp_config import SmtpConfig
import smtplib
from email.message import EmailMessage
from email.utils import formataddr
from urllib.request import urlopen
import fitz  # PyMuPDF
import io

bp = Blueprint("sales", __name__, url_prefix="/api/sales")


def _lab() -> Laboratory:
    claims = get_jwt() or {}
    tid = claims.get("tenant_id")
    if tid and tid != "default":
        try:
            return Laboratory.objects.get(id=tid)
        except Exception:
            pass
    lab = Laboratory.objects.first()
    if not lab:
        lab = Laboratory(name="Default Lab").save()
    return lab


def _calc_total(lines):
    total = 0.0  # sum after line discounts
    out = []
    # support per-line discounts (discount_rate % or discount_amount)
    for ln in lines or []:
        qty = float(ln.get("qty") or 0)
        price = float(ln.get("price") or 0)
        gross = qty * price
        disc = 0.0
        try:
            if ln.get('discount_amount') not in (None, ''):
                da = float(ln.get('discount_amount') or 0)
                disc = da
            elif ln.get('discount_rate') not in (None, ''):
                dr = float(ln.get('discount_rate') or 0)
                disc = gross * (dr/100.0)
        except Exception:
            disc = 0.0
        disc = max(0.0, min(disc, gross))
        tot = gross - disc
        total += tot
        out.append({
            "description": ln.get("description"),
            "qty": qty,
            "price": price,
            "discount_rate": ln.get('discount_rate'),
            "discount_amount": ln.get('discount_amount'),
            "total": tot,
        })
    return total, out

def _labels_for(lang: str) -> dict:
    lang = (lang or '').lower()
    if lang.startswith('pt'):
        return {
            'date': 'Data', 'lab_tenant': 'Laboratório / Tenant', 'client': 'Cliente',
            'billing': 'Faturação', 'shipping': 'Envio', 'currency': 'Moeda',
            'terms': 'Condição', 'type': 'Tipo', 'form': 'Forma', 'method': 'Método',
            'lines': 'Linhas', 'total': 'Total', 'born': 'Nasc.', 'tax_id': 'NIF', 'subtotal':'Subtotal', 'tax':'IVA', 'grand_total':'Total',
            'description': 'Descrição', 'qty': 'Qtd', 'price': 'Preço', 'discount':'Desconto', 'line_discount':'Desconto linhas', 'global_discount':'Desconto global', 'subtotal_after_discount':'Subtotal', 'decimal': ','
        }
    if lang.startswith('es'):
        return {
            'date': 'Fecha', 'lab_tenant': 'Laboratorio / Tenant', 'client': 'Cliente',
            'billing': 'Facturación', 'shipping': 'Envío', 'currency': 'Moneda',
            'terms': 'Condición', 'type': 'Tipo', 'form': 'Forma', 'method': 'Método',
            'lines': 'Líneas', 'total': 'Total', 'born': 'Nac.', 'tax_id': 'NIF',
            'description': 'Descripción', 'qty': 'Cant.', 'price': 'Precio', 'discount':'Descuento', 'line_discount':'Desc. líneas', 'global_discount':'Desc. global', 'subtotal_after_discount':'Subtotal', 'decimal': ','
        }
    if lang.startswith('fr'):
        return {
            'date': 'Date', 'lab_tenant': 'Laboratoire / Tenant', 'client': 'Client',
            'billing': 'Facturation', 'shipping': 'Expédition', 'currency': 'Devise',
            'terms': 'Condition', 'type': 'Type', 'form': 'Forme', 'method': 'Méthode',
            'lines': 'Lignes', 'total': 'Total', 'born': 'Né', 'tax_id': 'NIF',
            'description': 'Description', 'qty': 'Qté', 'price': 'Prix', 'discount':'Remise', 'line_discount':'Remise lignes', 'global_discount':'Remise globale', 'subtotal_after_discount':'Sous-total', 'decimal': ','
        }
    if lang.startswith('de'):
        return {
            'date': 'Datum', 'lab_tenant': 'Labor / Tenant', 'client': 'Kunde',
            'billing': 'Rechnung', 'shipping': 'Versand', 'currency': 'Währung',
            'terms': 'Bedingung', 'type': 'Typ', 'form': 'Formular', 'method': 'Methode',
            'lines': 'Positionen', 'total': 'Summe', 'born': 'Geb.', 'tax_id': 'USt-IdNr',
            'description': 'Beschreibung', 'qty': 'Menge', 'price': 'Preis', 'discount':'Rabatt', 'line_discount':'Zeilenrabatt', 'global_discount':'Globalrabatt', 'subtotal_after_discount':'Zwischensumme', 'decimal': ','
        }
    if lang.startswith('zh') or lang.startswith('cn'):
        return {
            'date': '日期', 'lab_tenant': '实验室 / 租户', 'client': '客户',
            'billing': '账单', 'shipping': '送货', 'currency': '货币',
            'terms': '条款', 'type': '类型', 'form': '形式', 'method': '方式',
            'lines': '明细', 'total': '合计', 'born': '出生', 'tax_id': '税号',
            'description': '描述', 'qty': '数量', 'price': '价格', 'discount':'折扣', 'line_discount':'行折扣', 'global_discount':'全局折扣', 'subtotal_after_discount':'小计', 'decimal': '.'
        }
    return {
        'date': 'Date', 'lab_tenant': 'Laboratory / Tenant', 'client': 'Client',
        'billing': 'Billing', 'shipping': 'Shipping', 'currency': 'Currency',
        'terms': 'Terms', 'type': 'Type', 'form': 'Form', 'method': 'Method', 'subtotal':'Subtotal', 'tax':'Tax', 'grand_total':'Total',
        'lines': 'Lines', 'total': 'Total', 'born': 'Born', 'tax_id': 'Tax ID',
        'description': 'Description', 'qty': 'Qty', 'price': 'Price', 'discount':'Discount', 'line_discount':'Line discount', 'global_discount':'Global discount', 'subtotal_after_discount':'Subtotal', 'decimal': '.'
    }
def _order_to_dict(o: Order):
    return {
        "id": str(o.id),
        "number": o.number,
        "date": o.date.isoformat() if o.date else None,
        "client": str(getattr(o.client, 'id', '') or ''),
        "client_code": getattr(o, 'client_code', None),
        "currency": o.currency,
        "lines": getattr(o, 'lines', []) or [],
        "total": o.total,
    }

def _invoice_to_dict(i: Invoice):
    return {
        "id": str(i.id),
        "number": i.number,
        "date": i.date.isoformat() if i.date else None,
        "client": str(getattr(i.client, 'id', '') or ''),
        "client_code": getattr(i, 'client_code', None),
        "currency": i.currency,
        "lines": getattr(i, 'lines', []) or [],
        "total": i.total,
        "status": i.status,
    }

def _render_pdf(
    title: str,
    number: str,
    date_str: str,
    currency: str,
    lines: list[dict],
    total: float,
    lab_info: dict | None = None,
    client_info: dict | None = None,
    labels: dict | None = None,
    tax_rate: float | None = None,
    tax_amount: float | None = None,
    discount_rate: float | None = None,
    discount_amount: float | None = None,
) -> bytes:
    labels = labels or {
        'date': 'Date', 'lab_tenant': 'Laboratory / Tenant', 'client': 'Client',
        'billing': 'Billing', 'shipping': 'Shipping', 'currency': 'Currency',
        'terms': 'Terms', 'type': 'Type', 'form': 'Form', 'method': 'Method',
        'lines': 'Lines', 'total': 'Total', 'born': 'Born', 'tax_id': 'Tax ID'
    }
    doc = fitz.open()
    page = doc.new_page()
    width, height = page.rect.width, page.rect.height

    # Header title centered and optional logo
    page.insert_text((width/2 - 150, 30), f"{title} {number}", fontsize=18)
    page.insert_text((width/2 - 150, 50), f"{labels.get('date','Date')}: {date_str}", fontsize=10)
    # Logo (top-left)
    try:
        logo_url = (lab_info or {}).get('logo_url')
        if logo_url:
            img_rect = fitz.Rect(30, 20, 110, 60)
            with urlopen(logo_url) as resp:
                img_bytes = resp.read()
                page.insert_image(img_rect, stream=img_bytes)
    except Exception:
        pass

    # Boxes
    # Lab box (top-left)
    lab_box = fitz.Rect(30, 70, width/2 - 10, 190)
    page.draw_rect(lab_box, color=(0,0,0), width=0.5)
    ty = lab_box.y0 + 10
    def _t(val):
        return str(val) if val is not None else ''
    if lab_info:
        page.insert_text((lab_box.x0+8, ty), _t(lab_info.get('name')), fontsize=11); ty += 12
        # Address in multiple lines
        addr = _t(lab_info.get('address')).strip()
        if addr:
            page.insert_text((lab_box.x0+8, ty), addr, fontsize=9); ty += 11
        pc_city = " ".join(filter(None, [_t(lab_info.get('postal_code')), _t(lab_info.get('city'))])).strip()
        if pc_city:
            page.insert_text((lab_box.x0+8, ty), pc_city, fontsize=9); ty += 11
        country = _t(lab_info.get('country'))
        if country:
            page.insert_text((lab_box.x0+8, ty), country, fontsize=9); ty += 11
        line3 = " | ".join(filter(None, [f"NIF: {_t(lab_info.get('tax_id'))}" if lab_info.get('tax_id') else '', _t(lab_info.get('phone')), _t(lab_info.get('email'))]))
        if line3:
            page.insert_text((lab_box.x0+8, ty), line3, fontsize=9); ty += 11
        page.insert_text((lab_box.x0+8, lab_box.y0+2), _t(labels.get('lab_tenant','Laboratory / Tenant')), fontsize=7)
        # extra rows if available
        extra = []
        if lab_info.get('id'):
            extra.append(f"ID: {_t(lab_info.get('id'))}")
        if extra:
            page.insert_text((lab_box.x0+8, lab_box.y1-12), " | ".join(extra), fontsize=7)

    # Client box (top-right)
    cli_box = fitz.Rect(width/2 + 10, 70, width - 30, 220)
    page.draw_rect(cli_box, color=(0,0,0), width=0.5)
    ty = cli_box.y0 + 10
    if client_info:
        title_line = " ".join(filter(None, [ _t(client_info.get('code')), _t(client_info.get('name')) ])).strip()
        page.insert_text((cli_box.x0+8, ty), title_line, fontsize=11); ty += 12
        # Identification
        id_line = " ".join(filter(None, [
            _t(client_info.get('type')),
            _t(client_info.get('gender')),
            f"{labels.get('born','Born')}: {_t(client_info.get('birthdate'))}" if client_info.get('birthdate') else ''
        ])).strip()
        if id_line:
            page.insert_text((cli_box.x0+8, ty), id_line, fontsize=9); ty += 11
        # Contacts - main address (multi-line)
        addr = _t(client_info.get('address')).strip()
        if addr:
            page.insert_text((cli_box.x0+8, ty), addr, fontsize=9); ty += 11
        # If client has 'address' split into lines like street|pc city|country when present
        line2 = " | ".join(filter(None, [f"{labels.get('tax_id','Tax ID')}: {_t(client_info.get('tax_id'))}" if client_info.get('tax_id') else '', _t(client_info.get('phone')), _t(client_info.get('email'))]))
        if line2:
            page.insert_text((cli_box.x0+8, ty), line2, fontsize=9); ty += 11
        # Billing/Shipping
        bill = client_info.get('billing_address') or {}
        ship = client_info.get('shipping_address') or {}
        if any(bill.values()):
            page.insert_text((cli_box.x0+8, ty), _t(labels.get('billing','Billing')+':' ), fontsize=8); ty += 10
            b_street = _t(bill.get('street')).strip()
            if b_street:
                page.insert_text((cli_box.x0+16, ty), b_street, fontsize=8); ty += 10
            b_pc_city = " ".join(filter(None, [_t(bill.get('postal_code')), _t(bill.get('city'))])).strip()
            if b_pc_city:
                page.insert_text((cli_box.x0+16, ty), b_pc_city, fontsize=8); ty += 10
            b_country = _t(bill.get('country')).strip()
            if b_country:
                page.insert_text((cli_box.x0+16, ty), b_country, fontsize=8); ty += 10
        if any(ship.values()):
            page.insert_text((cli_box.x0+8, ty), _t(labels.get('shipping','Shipping')+':' ), fontsize=8); ty += 10
            s_street = _t(ship.get('street')).strip()
            if s_street:
                page.insert_text((cli_box.x0+16, ty), s_street, fontsize=8); ty += 10
            s_pc_city = " ".join(filter(None, [_t(ship.get('postal_code')), _t(ship.get('city'))])).strip()
            if s_pc_city:
                page.insert_text((cli_box.x0+16, ty), s_pc_city, fontsize=8); ty += 10
            s_country = _t(ship.get('country')).strip()
            if s_country:
                page.insert_text((cli_box.x0+16, ty), s_country, fontsize=8); ty += 10
        # Financial preferences
        fin_parts = []
        if client_info.get('preferred_currency'):
            fin_parts.append(f"{labels.get('currency','Currency')}: {_t(client_info['preferred_currency'])}")
        if client_info.get('payment_terms'):
            fin_parts.append(f"{labels.get('terms','Terms')}: {_t(client_info['payment_terms'])}")
        if client_info.get('payment_type'):
            fin_parts.append(f"{labels.get('type','Type')}: {_t(client_info['payment_type'])}")
        if client_info.get('payment_form'):
            fin_parts.append(f"{labels.get('form','Form')}: {_t(client_info['payment_form'])}")
        if client_info.get('payment_method'):
            fin_parts.append(f"{labels.get('method','Method')}: {_t(client_info['payment_method'])}")
        if fin_parts:
            page.insert_text((cli_box.x0+8, ty), " | ".join(fin_parts), fontsize=8); ty += 10
        page.insert_text((cli_box.x0+8, cli_box.y0+2), _t(labels.get('client','Client')), fontsize=7)

    # Helpers
    def fmt(n: float) -> str:
        try:
            s = f"{n:.2f}"
            return s.replace('.', ',') if labels.get('decimal', ',') == ',' else s
        except Exception:
            return str(n)
    # Table section
    lm, rm, top = 30, width-30, 180
    y = top
    page.insert_text((lm, y), labels.get('lines','Lines')+':', fontsize=12); y += 14
    # Columns: desc 50%, qty 10%, price 15%, discount 10%, total 15%
    col_desc_w = (rm-lm)*0.50
    col_qty_w  = (rm-lm)*0.10
    col_price_w= (rm-lm)*0.15
    col_disc_w = (rm-lm)*0.10
    col_total_w= (rm-lm)*0.15
    x_desc = lm
    x_qty = lm + col_desc_w
    x_price = x_qty + col_qty_w
    x_disc = x_price + col_price_w
    x_total = x_disc + col_disc_w
    # Header row
    page.insert_text((x_desc, y), labels.get('description','Description'), fontsize=10)
    page.insert_text((x_qty, y), labels.get('qty','Qty'), fontsize=10)
    page.insert_text((x_price, y), labels.get('price','Price'), fontsize=10)
    page.insert_text((x_disc, y), labels.get('discount','Discount'), fontsize=10)
    page.insert_text((x_total, y), labels.get('total','Total'), fontsize=10)
    y += 12
    # Draw separator
    page.draw_line(p1=(lm, y), p2=(rm, y), width=0.5)
    y += 6
    # Rows
    def wrap_text(text: str, max_chars: int = 80):
        text = text or ''
        out = []
        while len(text) > max_chars:
            cut = text.rfind(' ', 0, max_chars)
            if cut == -1:
                cut = max_chars
            out.append(text[:cut].strip())
            text = text[cut:].strip()
        if text:
            out.append(text)
        return out
    sum_gross = 0.0
    sum_line_disc = 0.0
    for ln in lines or []:
        desc = str(ln.get('description') or '')
        qty = float(ln.get('qty') or 0)
        price = float(ln.get('price') or 0)
        gross = qty * price
        tot = float(ln.get('total') or gross)
        disc_val = max(0.0, gross - tot)
        sum_gross += gross
        sum_line_disc += disc_val
        wrapped = wrap_text(desc, int(col_desc_w/6))  # approx chars by width
        first = True
        for wline in wrapped or ['']:
            page.insert_text((x_desc, y), wline, fontsize=9)
            if first:
                page.insert_text((x_qty, y), fmt(qty), fontsize=9)
                page.insert_text((x_price, y), f"{fmt(price)} {currency}", fontsize=9)
                page.insert_text((x_disc, y), f"{fmt(disc_val)} {currency}", fontsize=9)
                page.insert_text((x_total, y), f"{fmt(tot)} {currency}", fontsize=9)
                first = False
            y += 12
            if y > height - 50:
                page = doc.new_page(); width, height = page.rect.width, page.rect.height
                y = 50
        # row separator
        page.draw_line(p1=(lm, y-4), p2=(rm, y-4), width=0.2)
    # Totals block
    y += 6
    # Subtotals and discounts
    page.insert_text((x_total-120, y), f"{labels.get('subtotal','Subtotal')}: {fmt(sum_gross)} {currency}", fontsize=10); y += 12
    if sum_line_disc > 0:
        page.insert_text((x_total-120, y), f"{labels.get('line_discount','Line discount')}: -{fmt(sum_line_disc)} {currency}", fontsize=10); y += 12
    # total here equals sum after line discounts
    page.insert_text((x_total-120, y), f"{labels.get('subtotal_after_discount','Subtotal')}: {fmt(total)} {currency}", fontsize=10); y += 12
    # Global discount (if any) computed on subtotal after line discounts
    gl_disc = 0.0
    if (discount_rate or 0) > 0:
        gl_disc = (discount_rate or 0.0) * total / 100.0
    if (discount_amount or 0) > 0:
        gl_disc = discount_amount or 0.0
    if gl_disc > 0:
        page.insert_text((x_total-120, y), f"{labels.get('global_discount','Discount')}: -{fmt(gl_disc)} {currency}", fontsize=10); y += 12
        total_after_global = max(0.0, total - gl_disc)
    else:
        total_after_global = total
    # Tax
    if (tax_rate or 0) > 0 or (tax_amount or 0) > 0:
        tr = tax_rate or 0.0
        ta = tax_amount if tax_amount is not None else (total_after_global*tr/100.0)
        page.insert_text((x_total-120, y), f"{labels.get('tax','Tax')}: {fmt(ta)} {currency} ({fmt(tr)}%)", fontsize=10); y += 12
    # Grand total
    grand = total_after_global + (tax_amount if tax_amount is not None else 0.0)
    page.insert_text((x_total-120, y), f"{labels.get('grand_total','Total')}: {fmt(grand)} {currency}", fontsize=12)
    # Footer with page numbers
    page_count = doc.page_count
    for i in range(page_count):
        p = doc.load_page(i)
        pw, ph = p.rect.width, p.rect.height
        p.insert_text((pw/2 - 30, ph - 20), f"{i+1}/{page_count}", fontsize=8)
        p.insert_text((30, ph - 20), f"{title} {number}", fontsize=8)
        p.insert_text((pw - 160, ph - 20), datetime.now().strftime('%Y-%m-%d %H:%M'), fontsize=8)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes

def _lab_to_info(lab: Laboratory | None) -> dict:
    if not lab:
        return {}
    return {
        "name": getattr(lab, 'name', ''),
        "id": str(getattr(lab, 'id', '')),
        "address": getattr(lab, 'address', ''),
        "postal_code": getattr(lab, 'postal_code', ''),
        "city": getattr(lab, 'city', ''),
        "country": getattr(lab, 'country', ''),
        "tax_id": getattr(lab, 'tax_id', ''),
        "email": getattr(lab, 'email', ''),
        "phone": getattr(lab, 'phone', ''),
    }

def _client_to_info(c: Client | None) -> dict:
    if not c:
        return {}
    # Resolve financial preference names
    cur = None; pt = None; pf = None; pm = None
    try:
        if getattr(c, 'preferred_currency', None):
            cur = Currency.objects.get(id=c.preferred_currency.id)
    except Exception:
        cur = None
    try:
        if getattr(c, 'payment_type', None):
            pt = PaymentType.objects.get(id=c.payment_type.id)
    except Exception:
        pt = None
    try:
        if getattr(c, 'payment_form', None):
            pf = PaymentForm.objects.get(id=c.payment_form.id)
    except Exception:
        pf = None
    try:
        if getattr(c, 'payment_method', None):
            pm = PaymentMethod.objects.get(id=c.payment_method.id)
    except Exception:
        pm = None
    return {
        "code": getattr(c, 'code', ''),
        "name": (f"{getattr(c,'first_name','') or ''} {getattr(c,'last_name','') or ''}".strip() or getattr(c, 'name', '')),
        "first_name": getattr(c, 'first_name', ''),
        "last_name": getattr(c, 'last_name', ''),
        "gender": getattr(c, 'gender', ''),
        "birthdate": getattr(c, 'birthdate', None).isoformat() if getattr(c, 'birthdate', None) else '',
        "type": getattr(c, 'type', ''),
        "tax_id": getattr(c, 'tax_id', ''),
        "email": getattr(c, 'email', ''),
        "phone": getattr(c, 'phone', ''),
        "address": getattr(c, 'address', ''),
        "billing_address": getattr(c, 'billing_address', {}) or {},
        "shipping_address": getattr(c, 'shipping_address', {}) or {},
        "payment_terms": getattr(c, 'payment_terms', ''),
        "preferred_currency": (getattr(cur, 'code', None) or getattr(cur, 'name', None) or None),
        "payment_type": getattr(pt, 'name', None),
        "payment_form": getattr(pf, 'name', None),
        "payment_method": getattr(pm, 'name', None),
    }

def _pdf_response(filename: str, content: bytes):
    bio = io.BytesIO(content)
    bio.seek(0)
    return send_file(bio, mimetype='application/pdf', as_attachment=False, download_name=filename)

# Orders
@bp.get("/orders")
@jwt_required()
def orders_list():
    lab = _lab()
    items = Order.objects(lab=lab).order_by("-date")
    return jsonify({"items": [{"id": str(o.id), "number": o.number, "date": o.date.isoformat() if o.date else None, "total": o.total} for o in items]})

@bp.get("/orders/<oid>")
@jwt_required()
def orders_get(oid):
    lab = _lab()
    o = Order.objects.get(id=oid, lab=lab)
    return jsonify({"order": _order_to_dict(o)})

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
        # create a simple one-time series
        ser = Series(lab=lab, doc_type=doc_type, prefix=fallback_prefix, next_number=1, padding=5, active=True).save()
    # atomic inc
    Series.objects(id=ser.id).update_one(inc__next_number=1)
    ser.reload()
    num = ser.next_number - 1
    number = f"{ser.prefix}{num:0{ser.padding}d}"
    return number, ser


@bp.post("/orders")
@jwt_required()
def orders_create():
    lab = _lab()
    data = request.get_json(force=True, silent=True) or {}
    # Client required
    cli_id = (data.get("client") or '').strip()
    if not cli_id:
        return jsonify({"error": "client required"}), 400
    try:
        cli = Client.objects.get(id=cli_id, lab=lab)
    except Exception:
        return jsonify({"error": "client not found"}), 404
    total, lines = _calc_total(data.get("lines"))
    number = data.get("number")
    series_id = data.get("series")
    if not number:
        number, ser = _next_number(lab, "order", series_id, "ORD-")
    currency = (data.get("currency") or "").strip()
    if not currency:
        try:
            if getattr(cli, 'preferred_currency', None) and getattr(cli.preferred_currency, 'code', None):
                currency = cli.preferred_currency.code
        except Exception:
            pass
    # Discounts/Taxes/notes
    discount_rate = float(data.get('discount_rate') or 0.0)
    discount_amount = float(data.get('discount_amount') or 0.0)
    tax_rate = float(data.get('tax_rate') or 0.0)
    # apply global discount to tax base
    base_after_global = total - (discount_amount if discount_amount>0 else (total*discount_rate/100.0))
    if base_after_global < 0: base_after_global = 0.0
    tax_amount = float(data.get('tax_amount') or (base_after_global*tax_rate/100.0)) if tax_rate else float(data.get('tax_amount') or 0.0)
    o = Order(lab=lab, number=number, date=data.get("date") or date.today(), client=cli, client_code=getattr(cli,'code', None) or '', currency= currency or "EUR", lines=lines, total=total, notes=data.get('notes') or '', discount_rate=discount_rate, discount_amount=discount_amount, tax_rate=tax_rate, tax_amount=tax_amount).save()
    return jsonify({"order_id": str(o.id), "total": total}), 201

@bp.put("/orders/<oid>")
@jwt_required()
def orders_update(oid):
    lab = _lab()
    data = request.get_json(force=True, silent=True) or {}
    try:
        o = Order.objects.get(id=oid, lab=lab)
    except Exception:
        return jsonify({"error": "not found"}), 404
    # optional client change
    if data.get("client"):
        try:
            cli = Client.objects.get(id=data.get("client"), lab=lab)
            o.client = cli
            o.client_code = getattr(cli, 'code', '') or ''
        except Exception:
            pass
    # lines and totals
    if "lines" in data:
        total, lines = _calc_total(data.get("lines"))
        o.lines = lines
        o.total = total
    # header fields
    for f in ["number","date","currency","notes"]:
        if f in data:
            setattr(o, f, data.get(f))
    # discounts/taxes
    if "discount_rate" in data:
        try: o.discount_rate = float(data.get('discount_rate') or 0.0)
        except Exception: pass
    if "discount_amount" in data:
        try: o.discount_amount = float(data.get('discount_amount') or 0.0)
        except Exception: pass
    if "tax_rate" in data:
        try: o.tax_rate = float(data.get('tax_rate') or 0.0)
        except Exception: pass
    # recompute tax based on updated base
    base_after_global = o.total - (o.discount_amount if (getattr(o,'discount_amount',0.0) or 0)>0 else (o.total * ((getattr(o,'discount_rate',0.0) or 0)/100.0)))
    if base_after_global < 0: base_after_global = 0.0
    if "tax_amount" in data and data.get('tax_amount') is not None:
        try: o.tax_amount = float(data.get('tax_amount') or 0.0)
        except Exception: pass
    else:
        o.tax_amount = base_after_global * ((getattr(o,'tax_rate',0.0) or 0)/100.0)
    o.save()
    return jsonify({"order": _order_to_dict(o)})

@bp.get("/orders/<oid>/pdf")
@jwt_required()
def orders_pdf(oid):
    try:
        lab = _lab()
        o = Order.objects.get(id=oid, lab=lab)
        c_obj = None
        try:
            if getattr(o, 'client', None):
                c_obj = Client.objects.get(id=o.client.id)
        except Exception:
            c_obj = None
        labels = _labels_for(request.headers.get('Accept-Language',''))
        pdf = _render_pdf(
            "Encomenda",
            o.number or '',
            o.date.isoformat() if o.date else '',
            o.currency or 'EUR',
            o.lines or [],
            float(o.total or 0),
            lab_info=_lab_to_info(lab),
            client_info=_client_to_info(c_obj),
            labels=labels,
            tax_rate=float(getattr(o,'tax_rate',0.0) or 0.0),
            tax_amount=float(getattr(o,'tax_amount',0.0) or 0.0),
            discount_rate=float(getattr(o,'discount_rate',0.0) or 0.0),
            discount_amount=float(getattr(o,'discount_amount',0.0) or 0.0),
        )
        return _pdf_response(f"order_{o.number or oid}.pdf", pdf)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.post("/orders/<oid>/email")
@jwt_required()
def orders_email(oid):
    lab = _lab()
    data = request.get_json(force=True, silent=True) or {}
    to_raw = (data.get('to') or '').strip()
    cc_raw = (data.get('cc') or '').strip()
    bcc_raw = (data.get('bcc') or '').strip()
    o = Order.objects.get(id=oid, lab=lab)
    # generate pdf
    client_name = ''
    client_email = ''
    try:
        cli_id = None
        try:
            cli_id = str(getattr(getattr(o, 'client', None), 'id', '') or '')
        except Exception:
            cli_id = None
        if cli_id:
            try:
                c = Client.objects.get(id=cli_id)
                client_name = ((getattr(c, 'first_name', None) or '') + ' ' + (getattr(c, 'last_name', None) or '')).strip() or (c.name or '')
                client_email = c.email or ''
            except Exception:
                pass
    except Exception:
        pass
    labels = _labels_for(request.headers.get('Accept-Language',''))
    pdf = _render_pdf(
        "Encomenda",
        o.number or '',
        o.date.isoformat() if o.date else '',
        o.currency or 'EUR',
        o.lines or [],
        float(o.total or 0),
        lab_info=_lab_to_info(lab),
        client_info=_client_to_info(Client.objects.get(id=o.client.id)) if getattr(o,'client',None) else {},
        labels=labels,
        tax_rate=float(getattr(o,'tax_rate',0.0) or 0.0),
        tax_amount=float(getattr(o,'tax_amount',0.0) or 0.0),
    )
    filename = f"order_{o.number or oid}.pdf"
    # load smtp
    cfg = SmtpConfig.objects(lab=lab).first()
    if not cfg or not cfg.server:
        return jsonify({"error": "smtp not configured"}), 400
    if not (cfg.username or ''):
        # We require a valid sender address (use username as sender)
        return jsonify({"error": "smtp username (sender) missing"}), 400
    # Parse recipients (accept ; or , separators)
    def split_emails(s: str):
        parts = []
        for token in (s or '').replace(';', ',').split(','):
            token = (token or '').strip()
            if token:
                parts.append(token)
        return parts
    to_list = split_emails(to_raw) or ([client_email] if client_email else [])
    cc_list = split_emails(cc_raw)
    bcc_list = split_emails(bcc_raw)
    if not to_list and not cc_list and not bcc_list:
        return jsonify({"error": "no recipients"}), 400
    msg = EmailMessage()
    sender = cfg.username
    msg['Subject'] = f"Encomenda {o.number}"
    msg['From'] = sender or ''
    if to_list:
        msg['To'] = ', '.join(to_list)
    if cc_list:
        msg['Cc'] = ', '.join(cc_list)
    if bcc_list:
        msg['Bcc'] = ', '.join(bcc_list)
    body = (data.get('message') or '').strip() or f"Segue em anexo a encomenda {o.number}."
    msg.set_content(body)
    msg.add_attachment(pdf, maintype='application', subtype='pdf', filename=filename)

    def _try_send(use_ssl: bool, use_tls: bool, port: int | None):
        srv = None
        try:
            if use_ssl:
                srv = smtplib.SMTP_SSL(cfg.server, port or 465, timeout=15)
            else:
                srv = smtplib.SMTP(cfg.server, port or 587, timeout=15)
            srv.ehlo()
            if use_tls and not use_ssl:
                srv.starttls(); srv.ehlo()
            if cfg.username:
                srv.login(cfg.username, cfg.password or '')
            # Explicit recipients list for safety
            all_rcpts = to_list + cc_list + bcc_list
            srv.send_message(msg, from_addr=sender, to_addrs=all_rcpts)
            return True, None
        except Exception as ex:
            return False, f"{ex.__class__.__name__}: {str(ex)}"
        finally:
            try:
                if srv:
                    srv.quit()
            except Exception:
                pass

    combos = []
    def add_combo(u_ssl, u_tls, prt):
        key = (bool(u_ssl), bool(u_tls), int(prt) if prt else None)
        if key not in combos:
            combos.append(key)
    # try configured first
    add_combo(getattr(cfg, 'use_ssl', False), getattr(cfg, 'use_tls', False), getattr(cfg, 'port', None))
    # common fallbacks
    add_combo(True, False, 465)
    add_combo(False, True, 587)

    errors = []
    for u_ssl, u_tls, prt in combos:
        ok, err = _try_send(u_ssl, u_tls, prt)
        if ok:
            return jsonify({"ok": True})
        else:
            errors.append(f"ssl={u_ssl} tls={u_tls} port={prt or (465 if u_ssl else 587)} -> {err}")
    return jsonify({"error": "; ".join(errors) or "smtp send failed"}), 500

@bp.post("/orders/<oid>/convert")
@jwt_required()
def orders_convert_to_invoice(oid):
    """Create an invoice from an order, preserving lines, discounts and taxes.
    Optional payload: { "series": "<series_id>" } to select invoice series.
    """
    lab = _lab()
    try:
        o = Order.objects.get(id=oid, lab=lab)
    except Exception:
        return jsonify({"error": "order not found"}), 404
    data = request.get_json(force=True, silent=True) or {}
    # Determine next invoice number
    series_id = data.get("series")
    inv_number, _ = _next_number(lab, "invoice", series_id, "INV-")
    # Build invoice
    inv = Invoice(
        lab=lab,
        number=inv_number,
        date=date.today(),
        client=o.client,
        client_code=getattr(o, 'client_code', None) or '',
        currency=o.currency or "EUR",
        lines=getattr(o, 'lines', []) or [],
        total=float(getattr(o, 'total', 0.0) or 0.0),
        status="issued",
        notes=getattr(o, 'notes', '') or '',
        discount_rate=float(getattr(o, 'discount_rate', 0.0) or 0.0),
        discount_amount=float(getattr(o, 'discount_amount', 0.0) or 0.0),
        tax_rate=float(getattr(o, 'tax_rate', 0.0) or 0.0),
        tax_amount=float(getattr(o, 'tax_amount', 0.0) or 0.0),
    ).save()
    return jsonify({"invoice_id": str(inv.id), "number": inv.number}), 201

# Invoices
@bp.get("/invoices")
@jwt_required()
def invoices_list():
    lab = _lab()
    items = Invoice.objects(lab=lab).order_by("-date")
    return jsonify({"items": [{"id": str(i.id), "number": i.number, "date": i.date.isoformat() if i.date else None, "total": i.total, "status": i.status} for i in items]})

@bp.get("/invoices/<iid>")
@jwt_required()
def invoices_get(iid):
    lab = _lab()
    inv = Invoice.objects.get(id=iid, lab=lab)
    return jsonify({"invoice": _invoice_to_dict(inv)})

@bp.post("/invoices")
@jwt_required()
def invoices_create():
    lab = _lab()
    data = request.get_json(force=True, silent=True) or {}
    cli_id = (data.get("client") or '').strip()
    if not cli_id:
        return jsonify({"error": "client required"}), 400
    try:
        cli = Client.objects.get(id=cli_id, lab=lab)
    except Exception:
        return jsonify({"error": "client not found"}), 404
    total, lines = _calc_total(data.get("lines"))
    number = data.get("number")
    series_id = data.get("series")
    if not number:
        number, ser = _next_number(lab, "invoice", series_id, "INV-")
    currency = (data.get("currency") or "").strip()
    if not currency:
        try:
            if getattr(cli, 'preferred_currency', None) and getattr(cli.preferred_currency, 'code', None):
                currency = cli.preferred_currency.code
        except Exception:
            pass
    discount_rate = float(data.get('discount_rate') or 0.0)
    discount_amount = float(data.get('discount_amount') or 0.0)
    tax_rate = float(data.get('tax_rate') or 0.0)
    base_after_global = total - (discount_amount if discount_amount>0 else (total*discount_rate/100.0))
    if base_after_global < 0: base_after_global = 0.0
    tax_amount = float(data.get('tax_amount') or (base_after_global*tax_rate/100.0)) if tax_rate else float(data.get('tax_amount') or 0.0)
    inv = Invoice(lab=lab, number=number, date=data.get("date") or date.today(), client=cli, client_code=getattr(cli,'code', None) or '', currency= currency or "EUR", lines=lines, total=total, status=data.get("status") or "draft", notes=data.get('notes') or '', discount_rate=discount_rate, discount_amount=discount_amount, tax_rate=tax_rate, tax_amount=tax_amount).save()
    return jsonify({"invoice_id": str(inv.id), "total": total}), 201

@bp.put("/invoices/<iid>")
@jwt_required()
def invoices_update(iid):
    lab = _lab()
    data = request.get_json(force=True, silent=True) or {}
    try:
        inv = Invoice.objects.get(id=iid, lab=lab)
    except Exception:
        return jsonify({"error": "not found"}), 404
    if data.get("client"):
        try:
            cli = Client.objects.get(id=data.get("client"), lab=lab)
            inv.client = cli
            inv.client_code = getattr(cli, 'code', '') or ''
        except Exception:
            pass
    if "lines" in data:
        total, lines = _calc_total(data.get("lines"))
        inv.lines = lines
        inv.total = total
    for f in ["number","date","currency","status","notes"]:
        if f in data:
            setattr(inv, f, data.get(f))
    if "discount_rate" in data:
        try: inv.discount_rate = float(data.get('discount_rate') or 0.0)
        except Exception: pass
    if "discount_amount" in data:
        try: inv.discount_amount = float(data.get('discount_amount') or 0.0)
        except Exception: pass
    if "tax_rate" in data:
        try: inv.tax_rate = float(data.get('tax_rate') or 0.0)
        except Exception: pass
    base_after_global = inv.total - (inv.discount_amount if (getattr(inv,'discount_amount',0.0) or 0)>0 else (inv.total * ((getattr(inv,'discount_rate',0.0) or 0)/100.0)))
    if base_after_global < 0: base_after_global = 0.0
    if "tax_amount" in data and data.get('tax_amount') is not None:
        try: inv.tax_amount = float(data.get('tax_amount') or 0.0)
        except Exception: pass
    else:
        inv.tax_amount = base_after_global * ((getattr(inv,'tax_rate',0.0) or 0)/100.0)
    inv.save()
    return jsonify({"invoice": _invoice_to_dict(inv)})

@bp.get("/invoices/<iid>/pdf")
@jwt_required()
def invoices_pdf(iid):
    try:
        lab = _lab()
        inv = Invoice.objects.get(id=iid, lab=lab)
        c_obj = None
        try:
            if getattr(inv, 'client', None):
                c_obj = Client.objects.get(id=inv.client.id)
        except Exception:
            c_obj = None
        labels = _labels_for(request.headers.get('Accept-Language',''))
        pdf = _render_pdf(
            "Fatura",
            inv.number or '',
            inv.date.isoformat() if inv.date else '',
            inv.currency or 'EUR',
            inv.lines or [],
            float(inv.total or 0),
            lab_info=_lab_to_info(lab),
            client_info=_client_to_info(c_obj),
            labels=labels,
            tax_rate=float(getattr(inv,'tax_rate',0.0) or 0.0),
            tax_amount=float(getattr(inv,'tax_amount',0.0) or 0.0),
            discount_rate=float(getattr(inv,'discount_rate',0.0) or 0.0),
            discount_amount=float(getattr(inv,'discount_amount',0.0) or 0.0),
        )
        return _pdf_response(f"invoice_{inv.number or iid}.pdf", pdf)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.post("/invoices/<iid>/email")
@jwt_required()
def invoices_email(iid):
    lab = _lab()
    data = request.get_json(force=True, silent=True) or {}
    to_raw = (data.get('to') or '').strip()
    cc_raw = (data.get('cc') or '').strip()
    bcc_raw = (data.get('bcc') or '').strip()
    inv = Invoice.objects.get(id=iid, lab=lab)
    client_name = ''
    client_email = ''
    try:
        cli_id = None
        try:
            cli_id = str(getattr(getattr(inv, 'client', None), 'id', '') or '')
        except Exception:
            cli_id = None
        if cli_id:
            try:
                c = Client.objects.get(id=cli_id)
                client_name = ((getattr(c, 'first_name', None) or '') + ' ' + (getattr(c, 'last_name', None) or '')).strip() or (c.name or '')
                client_email = c.email or ''
            except Exception:
                pass
    except Exception:
        pass
    labels = _labels_for(request.headers.get('Accept-Language',''))
    pdf = _render_pdf(
        "Fatura",
        inv.number or '',
        inv.date.isoformat() if inv.date else '',
        inv.currency or 'EUR',
        inv.lines or [],
        float(inv.total or 0),
        lab_info=_lab_to_info(lab),
        client_info=_client_to_info(Client.objects.get(id=inv.client.id)) if getattr(inv,'client',None) else {},
        labels=labels,
        tax_rate=float(getattr(inv,'tax_rate',0.0) or 0.0),
        tax_amount=float(getattr(inv,'tax_amount',0.0) or 0.0),
    )
    filename = f"invoice_{inv.number or iid}.pdf"
    cfg = SmtpConfig.objects(lab=lab).first()
    if not cfg or not cfg.server:
        return jsonify({"error": "smtp not configured"}), 400
    if not (cfg.username or ''):
        return jsonify({"error": "smtp username (sender) missing"}), 400
    def split_emails(s: str):
        parts = []
        for token in (s or '').replace(';', ',').split(','):
            token = (token or '').strip()
            if token:
                parts.append(token)
        return parts
    to_list = split_emails(to_raw) or ([client_email] if client_email else [])
    cc_list = split_emails(cc_raw)
    bcc_list = split_emails(bcc_raw)
    if not to_list and not cc_list and not bcc_list:
        return jsonify({"error": "no recipients"}), 400

    msg = EmailMessage()
    sender = cfg.username
    msg['Subject'] = f"Fatura {inv.number}"
    msg['From'] = sender or ''
    if to_list:
        msg['To'] = ', '.join(to_list)
    if cc_list:
        msg['Cc'] = ', '.join(cc_list)
    if bcc_list:
        msg['Bcc'] = ', '.join(bcc_list)
    body = (data.get('message') or '').strip() or f"Segue em anexo a fatura {inv.number}."
    msg.set_content(body)
    msg.add_attachment(pdf, maintype='application', subtype='pdf', filename=filename)

    def _try_send(use_ssl: bool, use_tls: bool, port: int | None):
        srv = None
        try:
            if use_ssl:
                srv = smtplib.SMTP_SSL(cfg.server, port or 465, timeout=15)
            else:
                srv = smtplib.SMTP(cfg.server, port or 587, timeout=15)
            srv.ehlo()
            if use_tls and not use_ssl:
                srv.starttls(); srv.ehlo()
            if cfg.username:
                srv.login(cfg.username, cfg.password or '')
            all_rcpts = to_list + cc_list + bcc_list
            srv.send_message(msg, from_addr=sender, to_addrs=all_rcpts)
            return True, None
        except Exception as ex:
            return False, f"{ex.__class__.__name__}: {str(ex)}"
        finally:
            try:
                if srv:
                    srv.quit()
            except Exception:
                pass

    combos = []
    def add_combo(u_ssl, u_tls, prt):
        key = (bool(u_ssl), bool(u_tls), int(prt) if prt else None)
        if key not in combos:
            combos.append(key)
    add_combo(getattr(cfg, 'use_ssl', False), getattr(cfg, 'use_tls', False), getattr(cfg, 'port', None))
    add_combo(True, False, 465)
    add_combo(False, True, 587)

    errors = []
    for u_ssl, u_tls, prt in combos:
        ok, err = _try_send(u_ssl, u_tls, prt)
        if ok:
            return jsonify({"ok": True})
        else:
            errors.append(f"ssl={u_ssl} tls={u_tls} port={prt or (465 if u_ssl else 587)} -> {err}")
    return jsonify({"error": "; ".join(errors) or "smtp send failed"}), 500
