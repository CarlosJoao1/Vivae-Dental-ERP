# backend/models/user.py
from mongoengine import Document, StringField, ReferenceField, DictField, ListField
from werkzeug.security import generate_password_hash, check_password_hash
from .laboratory import Laboratory

class User(Document):
    meta = {"collection": "users"}
    username = StringField(required=True, unique=True)
    email = StringField()
    # roles: sysadmin|admin|manager|operator|user
    role = StringField(default="admin")
    password_hash = StringField(required=True)
    tenant_id = ReferenceField(Laboratory, required=False)
    # List of laboratories this user can access (non-sysadmin filtered by this).
    allowed_labs = ListField(ReferenceField(Laboratory), default=list)
    # Armazena preferências por utilizador (UI, etc.)
    preferences = DictField(default=dict)

    def set_password(self, raw: str):
        self.password_hash = generate_password_hash(raw)

    def check_password(self, raw: str) -> bool:
        return check_password_hash(self.password_hash, raw)

    @property
    def is_sysadmin(self) -> bool:
        return (self.role or "").lower() == "sysadmin"
