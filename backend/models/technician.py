from mongoengine import StringField, ReferenceField
from .base import BaseDoc
from .laboratory import Laboratory

class Technician(BaseDoc):
    lab = ReferenceField(Laboratory, required=True)
    name = StringField(required=True, max_length=200)
    email = StringField()
    phone = StringField()
    workcenter = StringField()
