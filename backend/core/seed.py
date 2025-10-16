# backend/core/seed.py
from models.user import User
from models.laboratory import Laboratory
from models.technician import Technician
from models.service import Service
from models.patient import Patient
from models.client import Client
from models.currency import Currency
from models.payment_type import PaymentType
from models.payment_form import PaymentForm
from models.payment_method import PaymentMethod
from models.series import Series

def run_seed():
    # Lab
    lab = Laboratory.objects(name="Vivae Dental Lab").first()
    if not lab:
        lab = Laboratory(name="Vivae Dental Lab", country="PT", city="Oliveira do Hospital").save()
        print("✅ Seed: Laboratory created")
    else:
        print("ℹ️ Seed: Laboratory exists")

    # Admin user
    admin = User.objects(username="admin").first()
    if not admin:
        admin = User(username="admin", email="admin@local", role="admin", tenant_id=lab)
        admin.set_password("admin123")
        admin.save()
        print("✅ Seed: Admin user created (admin/admin123)")
    else:
        print("ℹ️ Seed: Admin user exists")

    # Technician
    tech = Technician.objects(lab=lab, name="Default Technician").first()
    if not tech:
        Technician(lab=lab, name="Default Technician", email="tech@local").save()
        print("✅ Seed: Technician created")
    else:
        print("ℹ️ Seed: Technician exists")

    # Service
    svc = Service.objects(lab=lab, code="CONS").first()
    if not svc:
        Service(lab=lab, name="Consulta", code="CONS", price=30.0).save()
        print("✅ Seed: Service created")
    else:
        print("ℹ️ Seed: Service exists")

    # Helper to get next formatted number for a series (atomic increment)
    def _next_number(lab_obj: Laboratory, doc_type: str, fallback_prefix: str) -> str:
        ser = Series.objects(lab=lab_obj, doc_type=doc_type, active=True).first()
        if not ser:
            ser = Series(lab=lab_obj, doc_type=doc_type, prefix=fallback_prefix, next_number=1, padding=5, active=True).save()
        Series.objects(id=ser.id).update_one(inc__next_number=1)
        ser.reload()
        num = (ser.next_number or 1) - 1
        return f"{ser.prefix}{num:0{ser.padding}d}"

    # Client (idempotent): ensure a default client with auto-generated code exists
    try:
        cli = Client.objects(lab=lab, name="Clínica Central").first()
        if not cli:
            code = _next_number(lab, "client", "CLI-")
            Client(
                lab=lab,
                code=code,
                name="Clínica Central",
                type="clinic",
                tax_id="PT999999990",
                email="contato@clinica.pt",
            ).save()
            print("✅ Seed: Client created")
        else:
            print("ℹ️ Seed: Client exists")
    except Exception as e:
        print(f"⚠️ Seed Client skipped: {e}")

    # Patient
    pat = Patient.objects(lab=lab, name="Paciente Demo").first()
    if not pat:
        Patient(lab=lab, name="Paciente Demo", email="paciente@local").save()
        print("✅ Seed: Patient created")
    else:
        print("ℹ️ Seed: Patient exists")

    # Financial defaults
    try:
        cur_eur = Currency.objects(lab=lab, code="EUR").first()
        if not cur_eur:
            Currency(lab=lab, code="EUR", name="Euro", symbol="€", is_default=True).save()
            print("✅ Seed: Currency EUR")
        cur_usd = Currency.objects(lab=lab, code="USD").first()
        if not cur_usd:
            Currency(lab=lab, code="USD", name="US Dollar", symbol="$", is_default=False).save()
            print("✅ Seed: Currency USD")

        if not PaymentType.objects(lab=lab, name="Immediate").first():
            PaymentType(lab=lab, code="IMM", name="Immediate").save()
        if not PaymentType.objects(lab=lab, name="30 Days").first():
            PaymentType(lab=lab, code="NET30", name="30 Days").save()

        if not PaymentForm.objects(lab=lab, name="Invoice").first():
            PaymentForm(lab=lab, code="INV", name="Invoice").save()
        if not PaymentForm.objects(lab=lab, name="Receipt").first():
            PaymentForm(lab=lab, code="REC", name="Receipt").save()

        if not PaymentMethod.objects(lab=lab, name="Cash").first():
            PaymentMethod(lab=lab, code="CASH", name="Cash").save()
        if not PaymentMethod.objects(lab=lab, name="Card").first():
            PaymentMethod(lab=lab, code="CARD", name="Card").save()
        if not PaymentMethod.objects(lab=lab, name="Bank Transfer").first():
            PaymentMethod(lab=lab, code="BT", name="Bank Transfer").save()
        print("✅ Seed: Financial masterdata")
    except Exception as e:
        print(f"⚠️ Seed Financial skipped: {e}")

    # Default series for orders and invoices
    try:
        if not Series.objects(lab=lab, doc_type="order").first():
            Series(lab=lab, doc_type="order", prefix="ORD-", next_number=1, padding=5, active=True).save()
            print("✅ Seed: Series ORD-")
        if not Series.objects(lab=lab, doc_type="invoice").first():
            Series(lab=lab, doc_type="invoice", prefix="INV-", next_number=1, padding=5, active=True).save()
            print("✅ Seed: Series INV-")
        if not Series.objects(lab=lab, doc_type="client").first():
            Series(lab=lab, doc_type="client", prefix="CLI-", next_number=1, padding=5, active=True).save()
            print("✅ Seed: Series CLI-")
    except Exception as e:
        print(f"⚠️ Seed Series skipped: {e}")
