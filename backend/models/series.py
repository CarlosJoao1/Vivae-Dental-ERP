from mongoengine import StringField, IntField, BooleanField, ReferenceField
from .base import BaseDoc
from .laboratory import Laboratory

class Series(BaseDoc):
    lab = ReferenceField(Laboratory, required=True)
    doc_type = StringField(required=True, choices=("order","invoice","client"))
    prefix = StringField(default="")
    next_number = IntField(default=1)
    padding = IntField(default=5)
    active = BooleanField(default=True)
