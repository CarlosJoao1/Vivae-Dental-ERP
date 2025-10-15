"""
Migration: set client.code for existing clients and backfill client_code on orders/invoices
"""
import os
import sys
from pathlib import Path
from mongoengine import connect

# Ensure project root (/app) is on sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from models.laboratory import Laboratory
from models.client import Client
from models.series import Series
from models.order import Order
from models.invoice import Invoice

def next_number(lab, doc_type: str, fallback_prefix: str) -> str:
    ser = Series.objects(lab=lab, doc_type=doc_type, active=True).first()
    if not ser:
        ser = Series(lab=lab, doc_type=doc_type, prefix=fallback_prefix, next_number=1, padding=5, active=True).save()
    Series.objects(id=ser.id).update_one(inc__next_number=1)
    ser.reload()
    num = ser.next_number - 1
    return f"{ser.prefix}{num:0{ser.padding}d}"

def run():
    uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/vivae_dental_erp")
    connect(host=uri, alias="default")
    print(f"Connected to {uri}")

    labs = Laboratory.objects()
    for lab in labs:
        print(f"Lab: {lab.name}")
        # Ensure DB-level unique index on (lab, code)
        try:
            Client._get_collection().create_index([('lab', 1), ('code', 1)], unique=True, name='lab_code_unique')
            print("  + Ensured unique index on (lab, code)")
        except Exception as e:
            print(f"  ! Index ensure failed/skipped: {e}")
        # Ensure client series
        ser = Series.objects(lab=lab, doc_type="client").first()
        if not ser:
            Series(lab=lab, doc_type="client", prefix="CLI-", next_number=1, padding=5, active=True).save()
            print("  + Created client series CLI-")
        else:
            if ser.prefix != "CLI-":
                ser.prefix = "CLI-"
                ser.save()
                print("  ~ Updated client series prefix to CLI-")
        # Backfill client.code
        for c in Client.objects(lab=lab):
            if not getattr(c, 'code', None):
                c.code = next_number(lab, 'client', 'CLI-')
                try:
                    c.save()
                    print(f"  + Set client code {c.code} for {c.id}")
                except Exception as e:
                    print(f"  ! Failed to set code for client {c.id}: {e}")
        # Prepare fallback client
        fallback_client = None
        try:
            fallback_client = Client.objects(lab=lab, name="Unknown Client").first()
            if not fallback_client:
                code_val = next_number(lab, 'client', 'CLI-')
                fallback_client = Client(lab=lab, name="Unknown Client", type="other", email=None, code=code_val).save()
                print(f"  + Created fallback client {fallback_client.id} ({code_val})")
        except Exception as e:
            print(f"  ! Fallback client failed: {e}")

        # Backfill order.client_code
        for o in Order.objects(lab=lab):
            if not getattr(o, 'client_code', None):
                try:
                    if getattr(o, 'client', None):
                        cli = Client.objects.get(id=o.client.id)
                        o.client_code = getattr(cli, 'code', '') or ''
                        o.save()
                        print(f"  + Set order {o.id} client_code={o.client_code}")
                    else:
                        raise ValueError('no client')
                except Exception as e:
                    try:
                        if fallback_client:
                            o.client = fallback_client
                            o.client_code = getattr(fallback_client, 'code', '') or ''
                            o.save()
                            print(f"  ~ Fixed order {o.id} with fallback client")
                        else:
                            print(f"  ! Skip order {o.id}: {e}")
                    except Exception as e2:
                        print(f"  ! Skip order {o.id}: {e2}")
        # Backfill invoice.client_code
        for inv in Invoice.objects(lab=lab):
            if not getattr(inv, 'client_code', None):
                try:
                    if getattr(inv, 'client', None):
                        cli = Client.objects.get(id=inv.client.id)
                        inv.client_code = getattr(cli, 'code', '') or ''
                        inv.save()
                        print(f"  + Set invoice {inv.id} client_code={inv.client_code}")
                    else:
                        raise ValueError('no client')
                except Exception as e:
                    try:
                        if fallback_client:
                            inv.client = fallback_client
                            inv.client_code = getattr(fallback_client, 'code', '') or ''
                            inv.save()
                            print(f"  ~ Fixed invoice {inv.id} with fallback client")
                        else:
                            print(f"  ! Skip invoice {inv.id}: {e}")
                    except Exception as e2:
                        print(f"  ! Skip invoice {inv.id}: {e2}")

if __name__ == "__main__":
    run()
