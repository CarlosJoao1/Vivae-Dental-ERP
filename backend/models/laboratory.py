# backend/models/laboratory.py
from mongoengine import Document, StringField, BooleanField, DateTimeField
from datetime import datetime


class Laboratory(Document):
    meta = {"collection": "laboratory"}
    name = StringField(required=True, unique=True)
    address = StringField()
    country = StringField()
    postal_code = StringField()
    city = StringField()
    tax_id = StringField()
    phone = StringField()
    email = StringField()
    active = BooleanField(default=True)
    logo_url = StringField()

    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

    meta = {"collection": "laboratory"}

