# backend/core/seed.py
from models.user import User
from models.laboratory import Laboratory
from models.technician import Technician
from models.service import Service
from models.patient import Patient
from models.client import Client
from models.currency import Currency
from models.country import Country
from models.payment_type import PaymentType
from models.payment_form import PaymentForm
from models.payment_method import PaymentMethod
from models.series import Series
# Production models
from models.production.uom import UOM
from models.production.location import Location
from models.production.supplier import Supplier
from models.production.item import Item
from models.production.work_center import WorkCenter, MachineCenter
from models.production.bom import BOM, BOMLine
from models.production.routing import Routing, RoutingOperation
from models.production.production_order import ProductionOrder, ProductionOrderOperation

def run_seed():
    # Lab
    lab = Laboratory.objects(name="Vivae Dental Lab").first()
    if not lab:
        lab = Laboratory(name="Vivae Dental Lab", country="PT", city="Oliveira do Hospital").save()
        print("✅ Seed: Laboratory created")
    else:
        print("ℹ️ Seed: Laboratory exists")

    # Admin user — ensure sysadmin with universal access
    admin = User.objects(username="admin").first()
    if not admin:
        admin = User(username="admin", email="admin@local", role="sysadmin", tenant_id=lab)
        admin.set_password("admin123")
        admin.save()
        print("✅ Seed: Admin user created as sysadmin (admin/admin123)")
    else:
        # Upgrade existing admin to sysadmin if needed (idempotent)
        if (admin.role or "").lower() != "sysadmin":
            admin.role = "sysadmin"
            admin.save()
            print("✅ Seed: Admin user upgraded to sysadmin")
        else:
            print("ℹ️ Seed: Admin user exists and is sysadmin")

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

    # Countries seed (partial list)
    try:
        if Country.objects.count() == 0:
            pairs = [
                ("PT","Portugal"),("ES","España"),("FR","France"),("DE","Deutschland"),("IT","Italia"),
                ("GB","United Kingdom"),("US","United States"),("BR","Brasil"),("CN","China"),("JP","Japan"),
                ("NL","Nederland"),("BE","Belgium"),("LU","Luxembourg"),("IE","Ireland"),("CH","Switzerland"),
            ]
            for code,name in pairs:
                try:
                    Country(code=code, name=name).save()
                except Exception:
                    pass
    except Exception:
        pass

    # ========================================
    # PRODUCTION MODULE SEED DATA
    # ========================================
    print("\n🏭 Seeding Production Module Data...")
    
    try:
        # 1. Units of Measure (UOMs)
        uom_unit = UOM.objects(lab=lab, code="UNIT").first()
        if not uom_unit:
            uom_unit = UOM(lab=lab, code="UNIT", name="Unit", description="Single unit").save()
            print("✅ Production Seed: UOM Unit")
        
        uom_kg = UOM.objects(lab=lab, code="KG").first()
        if not uom_kg:
            uom_kg = UOM(lab=lab, code="KG", name="Kilogram", description="Weight in kg").save()
            print("✅ Production Seed: UOM Kilogram")
        
        uom_m = UOM.objects(lab=lab, code="M").first()
        if not uom_m:
            uom_m = UOM(lab=lab, code="M", name="Meter", description="Length in meters").save()
            print("✅ Production Seed: UOM Meter")

        # 2. Locations
        loc_main = Location.objects(lab=lab, code="MAIN-WH").first()
        if not loc_main:
            loc_main = Location(lab=lab, code="MAIN-WH", name="Main Warehouse", location_type="warehouse").save()
            print("✅ Production Seed: Location Main Warehouse")
        
        loc_prod = Location.objects(lab=lab, code="PROD-FLOOR").first()
        if not loc_prod:
            loc_prod = Location(lab=lab, code="PROD-FLOOR", name="Production Floor", location_type="production").save()
            print("✅ Production Seed: Location Production Floor")

        # 3. Supplier
        supplier = Supplier.objects(lab=lab, code="SUP-001").first()
        if not supplier:
            supplier = Supplier(
                lab=lab,
                code="SUP-001",
                name="Dental Materials Ltd",
                contact_person="John Smith",
                email="contact@dentalmaterials.com",
                phone="+351 234 567 890"
            ).save()
            print("✅ Production Seed: Supplier Dental Materials Ltd")

        # 4. Items (Products & Raw Materials)
        item_crown = Item.objects(lab=lab, item_no="CROWN-001").first()
        if not item_crown:
            item_crown = Item(
                lab=lab,
                item_no="CROWN-001",
                description="Ceramic Crown",
                item_type="finished_good",
                base_uom=uom_unit,
                standard_cost=50.0,
                list_price=150.0
            ).save()
            print("✅ Production Seed: Item Ceramic Crown")

        item_ceramic = Item.objects(lab=lab, item_no="MAT-CER-001").first()
        if not item_ceramic:
            item_ceramic = Item(
                lab=lab,
                item_no="MAT-CER-001",
                description="Ceramic Powder 1kg",
                item_type="raw_material",
                base_uom=uom_kg,
                standard_cost=25.0,
                list_price=35.0,
                supplier=supplier
            ).save()
            print("✅ Production Seed: Item Ceramic Powder")

        item_resin = Item.objects(lab=lab, item_no="MAT-RES-001").first()
        if not item_resin:
            item_resin = Item(
                lab=lab,
                item_no="MAT-RES-001",
                description="Dental Resin 500g",
                item_type="raw_material",
                base_uom=uom_kg,
                standard_cost=15.0,
                list_price=22.0,
                supplier=supplier
            ).save()
            print("✅ Production Seed: Item Dental Resin")

        # 5. Work Centers
        wc_molding = WorkCenter.objects(lab=lab, code="WC-MOLD").first()
        if not wc_molding:
            wc_molding = WorkCenter(
                lab=lab,
                code="WC-MOLD",
                name="Molding Station",
                work_center_type="manual",
                capacity=8.0,
                efficiency=95.0,
                location=loc_prod
            ).save()
            print("✅ Production Seed: Work Center Molding")

        wc_finishing = WorkCenter.objects(lab=lab, code="WC-FINISH").first()
        if not wc_finishing:
            wc_finishing = WorkCenter(
                lab=lab,
                code="WC-FINISH",
                name="Finishing Station",
                work_center_type="manual",
                capacity=8.0,
                efficiency=90.0,
                location=loc_prod
            ).save()
            print("✅ Production Seed: Work Center Finishing")

        # 6. Machine Center
        mc_kiln = MachineCenter.objects(lab=lab, code="MC-KILN-01").first()
        if not mc_kiln:
            mc_kiln = MachineCenter(
                lab=lab,
                code="MC-KILN-01",
                name="Ceramic Kiln #1",
                machine_type="kiln",
                capacity=4.0,
                work_center=wc_molding
            ).save()
            print("✅ Production Seed: Machine Center Kiln")

        # 7. Bill of Materials (BOM)
        bom = BOM.objects(lab=lab, item=item_crown, version="1.0").first()
        if not bom:
            bom = BOM(
                lab=lab,
                item=item_crown,
                version="1.0",
                status="certified",
                base_quantity=1.0,
                base_uom=uom_unit
            ).save()
            
            # BOM Lines
            BOMLine(
                bom=bom,
                line_no=10,
                component=item_ceramic,
                quantity=0.05,
                uom=uom_kg,
                scrap_percentage=5.0
            ).save()
            
            BOMLine(
                bom=bom,
                line_no=20,
                component=item_resin,
                quantity=0.02,
                uom=uom_kg,
                scrap_percentage=3.0
            ).save()
            
            print("✅ Production Seed: BOM for Ceramic Crown with 2 lines")

        # 8. Routing
        routing = Routing.objects(lab=lab, item=item_crown, version="1.0").first()
        if not routing:
            routing = Routing(
                lab=lab,
                item=item_crown,
                version="1.0",
                status="certified"
            ).save()
            
            # Routing Operations
            RoutingOperation(
                routing=routing,
                operation_no=10,
                work_center=wc_molding,
                description="Mold ceramic base",
                setup_time=30.0,
                run_time=60.0,
                machine_center=mc_kiln
            ).save()
            
            RoutingOperation(
                routing=routing,
                operation_no=20,
                work_center=wc_finishing,
                description="Polish and finish crown",
                setup_time=15.0,
                run_time=45.0
            ).save()
            
            print("✅ Production Seed: Routing for Ceramic Crown with 2 operations")

        # 9. Production Order (Demo)
        po = ProductionOrder.objects(lab=lab, order_no="PO-DEMO-001").first()
        if not po:
            po = ProductionOrder(
                lab=lab,
                order_no="PO-DEMO-001",
                item=item_crown,
                quantity=10.0,
                uom=uom_unit,
                status="released",
                bom=bom,
                routing=routing,
                location=loc_prod
            ).save()
            
            # Production Order Operations
            ProductionOrderOperation(
                production_order=po,
                operation_no=10,
                work_center=wc_molding,
                description="Mold ceramic base",
                setup_time=30.0,
                run_time=60.0,
                status="ready",
                machine_center=mc_kiln
            ).save()
            
            ProductionOrderOperation(
                production_order=po,
                operation_no=20,
                work_center=wc_finishing,
                description="Polish and finish crown",
                setup_time=15.0,
                run_time=45.0,
                status="ready"
            ).save()
            
            print("✅ Production Seed: Production Order PO-DEMO-001 with 2 operations")

        print("✅ Production Module seed completed successfully!\n")

    except Exception as e:
        print(f"⚠️ Production Seed error: {e}")
        import traceback
        traceback.print_exc()
