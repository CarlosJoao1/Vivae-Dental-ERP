# backend/core/seed.py
from models.user import User
from models.laboratory import Laboratory

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
