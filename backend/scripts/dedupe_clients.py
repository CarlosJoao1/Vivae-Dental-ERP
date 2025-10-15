# backend/scripts/dedupe_clients.py
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app import create_app
from models.client import Client
from models.laboratory import Laboratory

app = create_app()


def normalize_email(e: str | None) -> str | None:
    if not e:
        return None
    e = e.strip()
    return e.lower() or None


def run():
    with app.app_context():
        # DB connection is already initialized by create_app()

        removed = 0

        # Load all clients ordered by created_at to prefer keeping the oldest
        clients = list(Client.objects.order_by("created_at"))

        seen_email: set[tuple[str, str]] = set()
        seen_nif: set[tuple[str, str]] = set()

        to_delete: list[Client] = []

        for c in clients:
            lab_id = str(getattr(getattr(c, "lab", None), "id", "") or "")
            if not lab_id:
                continue

            # Deduplicate by (lab, email)
            em = normalize_email(getattr(c, "email", None))
            if em:
                key = (lab_id, em)
                if key in seen_email:
                    to_delete.append(c)
                else:
                    seen_email.add(key)

            # Deduplicate by (lab, tax_id)
            nif = (getattr(c, "tax_id", None) or "").strip()
            if nif:
                key2 = (lab_id, nif)
                if key2 in seen_nif:
                    to_delete.append(c)
                else:
                    seen_nif.add(key2)

        # Delete duplicates
        for c in to_delete:
            try:
                c.delete()
                removed += 1
            except Exception:
                pass

        # Recreate unique indexes (idempotent)
        try:
            col = Client._get_collection()
            col.create_index([('lab', 1), ('email', 1)], unique=True, sparse=True)
            col.create_index([('lab', 1), ('tax_id', 1)], unique=True, sparse=True)
            print("✅ Unique indexes ensured for Client (lab+email, lab+tax_id)")
        except Exception as e:
            print(f"⚠️ Could not ensure indexes: {e}")

        print(f"✅ Deduplication complete. Removed: {removed}")


if __name__ == "__main__":
    run()
