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
from models.production.uom import UnitOfMeasure
from models.production.location import Location
from models.production.supplier import Supplier
from models.production.item import Item
from models.production.work_center import WorkCenter, MachineCenter
from models.production.bom import BOM, BOMLine
from models.production.routing import Routing, RoutingOperation
from models.production.production_order import ProductionOrder, ProductionOrderLine, ProductionOrderRouting

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
        lab_id = str(lab.id)
        
        # 1. Units of Measure (UOMs)
        uom_unit = UnitOfMeasure.objects(tenant_id=lab, code="UNIT").first()
        if not uom_unit:
            uom_unit = UnitOfMeasure(tenant_id=lab, code="UNIT", description="Unit").save()
            print("✅ Production Seed: UOM Unit")
        
        uom_kg = UnitOfMeasure.objects(tenant_id=lab, code="KG").first()
        if not uom_kg:
            uom_kg = UnitOfMeasure(tenant_id=lab, code="KG", description="Kilogram").save()
            print("✅ Production Seed: UOM Kilogram")
        
        uom_m = UnitOfMeasure.objects(tenant_id=lab, code="M").first()
        if not uom_m:
            uom_m = UnitOfMeasure(tenant_id=lab, code="M", description="Meter").save()
            print("✅ Production Seed: UOM Meter")

        # 2. Locations
        loc_main = Location.objects(tenant_id=lab, code="MAIN-WH").first()
        if not loc_main:
            loc_main = Location(tenant_id=lab, code="MAIN-WH", name="Main Warehouse").save()
            print("✅ Production Seed: Location Main Warehouse")
        
        loc_prod = Location.objects(tenant_id=lab, code="PROD-FLOOR").first()
        if not loc_prod:
            loc_prod = Location(tenant_id=lab, code="PROD-FLOOR", name="Production Floor").save()
            print("✅ Production Seed: Location Production Floor")

        # 3. Supplier
        supplier = Supplier.objects(tenant_id=lab, supplier_id="SUP-001").first()
        if not supplier:
            supplier = Supplier(
                tenant_id=lab,
                supplier_id="SUP-001",
                name="Dental Materials Ltd",
                phone_no="+351 234 567 890",
                email="contact@dentalmaterials.com"
            ).save()
            print("✅ Production Seed: Supplier Dental Materials Ltd")

        # 4. Items (Products & Raw Materials)
        item_crown = Item.objects(tenant_id=lab, item_no="CROWN-001").first()
        if not item_crown:
            item_crown = Item(
                tenant_id=lab,
                item_no="CROWN-001",
                description="Ceramic Crown",
                item_type="manufactured",
                base_uom="UNIT"
            ).save()
            print("✅ Production Seed: Item Ceramic Crown")

        item_ceramic = Item.objects(tenant_id=lab, item_no="MAT-CER-001").first()
        if not item_ceramic:
            item_ceramic = Item(
                tenant_id=lab,
                item_no="MAT-CER-001",
                description="Ceramic Powder 1kg",
                item_type="purchased",
                base_uom="KG",
                default_supplier_id="SUP-001"
            ).save()
            print("✅ Production Seed: Item Ceramic Powder")

        item_resin = Item.objects(tenant_id=lab, item_no="MAT-RES-001").first()
        if not item_resin:
            item_resin = Item(
                tenant_id=lab,
                item_no="MAT-RES-001",
                description="Dental Resin 500g",
                item_type="purchased",
                base_uom="KG",
                default_supplier_id="SUP-001"
            ).save()
            print("✅ Production Seed: Item Dental Resin")

        # 5. Work Centers
        wc_molding = WorkCenter.objects(tenant_id=lab_id, code="WC-MOLD").first()
        if not wc_molding:
            wc_molding = WorkCenter(
                tenant_id=lab_id,
                code="WC-MOLD",
                name="Molding Station",
                work_center_type="Work Center",
                capacity=480.0,
                efficiency_pct=95.0,
                location_code="PROD-FLOOR"
            ).save()
            print("✅ Production Seed: Work Center Molding")

        wc_finishing = WorkCenter.objects(tenant_id=lab_id, code="WC-FINISH").first()
        if not wc_finishing:
            wc_finishing = WorkCenter(
                tenant_id=lab_id,
                code="WC-FINISH",
                name="Finishing Station",
                work_center_type="Work Center",
                capacity=480.0,
                efficiency_pct=90.0,
                location_code="PROD-FLOOR"
            ).save()
            print("✅ Production Seed: Work Center Finishing")

        # 6. Machine Center
        mc_kiln = MachineCenter.objects(tenant_id=lab_id, code="MC-KILN-01").first()
        if not mc_kiln:
            mc_kiln = MachineCenter(
                tenant_id=lab_id,
                code="MC-KILN-01",
                name="Ceramic Kiln #1",
                machine_center_type="Kiln",
                capacity=240.0,
                work_center_code="WC-MOLD"
            ).save()
            print("✅ Production Seed: Machine Center Kiln")

        # 7. Bill of Materials (BOM)
        bom = BOM.objects(tenant_id=lab_id, item_no="CROWN-001", version_code="V1").first()
        if not bom:
            bom_lines = [
                BOMLine(
                    line_no=10,
                    component_type="Item",
                    component_item_no="MAT-CER-001",
                    description="Ceramic Powder 1kg",
                    quantity_per=0.05,
                    uom_code="KG",
                    scrap_pct=5.0
                ),
                BOMLine(
                    line_no=20,
                    component_type="Item",
                    component_item_no="MAT-RES-001",
                    description="Dental Resin 500g",
                    quantity_per=0.02,
                    uom_code="KG",
                    scrap_pct=3.0
                )
            ]
            
            bom = BOM(
                tenant_id=lab_id,
                item_no="CROWN-001",
                version_code="V1",
                description="Ceramic Crown BOM",
                status="Certified",
                base_quantity=1.0,
                base_uom="UNIT",
                lines=bom_lines
            ).save()
            
            print("✅ Production Seed: BOM for Ceramic Crown with 2 lines")

        # 8. Routing
        routing = Routing.objects(tenant_id=lab_id, item_no="CROWN-001", version_code="V1").first()
        if not routing:
            routing_ops = [
                RoutingOperation(
                    operation_no=10,
                    work_center_code="WC-MOLD",
                    machine_center_code="MC-KILN-01",
                    description="Mold ceramic base",
                    setup_time=30.0,
                    run_time=60.0
                ),
                RoutingOperation(
                    operation_no=20,
                    work_center_code="WC-FINISH",
                    description="Polish and finish crown",
                    setup_time=15.0,
                    run_time=45.0
                )
            ]
            
            routing = Routing(
                tenant_id=lab_id,
                item_no="CROWN-001",
                version_code="V1",
                description="Ceramic Crown Routing",
                status="Certified",
                operations=routing_ops
            ).save()
            
            print("✅ Production Seed: Routing for Ceramic Crown with 2 operations")

        # 9. Production Order (Demo)
        po = ProductionOrder.objects(tenant_id=lab_id, order_no="PO-DEMO-001").first()
        if not po:
            # Create BOM lines from BOM
            po_lines = [
                ProductionOrderLine(
                    line_no=10,
                    component_item_no="MAT-CER-001",
                    description="Ceramic Powder 1kg",
                    quantity_per=0.05,
                    expected_quantity=0.5,  # 10 units * 0.05
                    remaining_quantity=0.5,
                    uom_code="KG",
                    location_code="MAIN-WH"
                ),
                ProductionOrderLine(
                    line_no=20,
                    component_item_no="MAT-RES-001",
                    description="Dental Resin 500g",
                    quantity_per=0.02,
                    expected_quantity=0.2,  # 10 units * 0.02
                    remaining_quantity=0.2,
                    uom_code="KG",
                    location_code="MAIN-WH"
                )
            ]
            
            # Create routing operations from Routing
            po_routing = [
                ProductionOrderRouting(
                    operation_no=10,
                    work_center_code="WC-MOLD",
                    machine_center_code="MC-KILN-01",
                    description="Mold ceramic base",
                    setup_time=30.0,
                    run_time=60.0,
                    expected_capacity_need=90.0,
                    remaining_time=90.0,
                    status="Planned"
                ),
                ProductionOrderRouting(
                    operation_no=20,
                    work_center_code="WC-FINISH",
                    description="Polish and finish crown",
                    setup_time=15.0,
                    run_time=45.0,
                    expected_capacity_need=60.0,
                    remaining_time=60.0,
                    status="Planned"
                )
            ]
            
            po = ProductionOrder(
                tenant_id=lab_id,
                order_no="PO-DEMO-001",
                description="Demo Production Order - Ceramic Crowns",
                item_no="CROWN-001",
                quantity=10.0,
                remaining_quantity=10.0,
                uom_code="UNIT",
                status="Released",
                bom_no="CROWN-001",
                bom_version_code="V1",
                routing_no="CROWN-001",
                routing_version_code="V1",
                location_code="PROD-FLOOR",
                lines=po_lines,
                routing_lines=po_routing
            ).save()
            
            print("✅ Production Seed: Production Order PO-DEMO-001 with 2 components and 2 operations")

        print("✅ Production Module seed completed successfully!\n")

    except Exception as e:
        print(f"⚠️ Production Seed error: {e}")
        import traceback
        traceback.print_exc()
