from mongoengine import Document, ReferenceField, DictField
from .laboratory import Laboratory


class RolePolicy(Document):
    meta = {"collection": "role_policies"}
    lab = ReferenceField(Laboratory, required=True, unique=True)
    # policies structure: { role: { feature: { action: bool } } }
    policies = DictField(default=dict)
