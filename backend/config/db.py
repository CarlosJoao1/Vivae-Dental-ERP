# backend/config/db.py
import os
from mongoengine import connect
from flask import current_app

def init_db(app):
    uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/vivae_dental_erp")
    connect(host=uri, alias="default")
    try:
        app.logger.info(f"Connected MongoDB: {uri}")
    except Exception:
        # app may not be active yet in some contexts
        pass
