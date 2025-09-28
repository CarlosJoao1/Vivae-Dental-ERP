# backend/models/user.py
from mongoengine import Document, StringField, ReferenceField
from werkzeug.security import generate_password_hash, check_password_hash
from .laboratory import Laboratory

class User(Document):
    meta = {"collection": "users"}
    username = StringField(required=True, unique=True)
    email = StringField()
    role = StringField(default="admin")  # admin|manager|operator
    password_hash = StringField(required=True)
    tenant_id = ReferenceField(Laboratory, required=False)

    def set_password(self, raw: str):
        self.password_hash = generate_password_hash(raw)

    def check_password(self, raw: str) -> bool:
        return check_password_hash(self.password_hash, raw)
