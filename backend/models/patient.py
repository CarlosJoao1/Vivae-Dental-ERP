from mongoengine import StringField, DateField, ReferenceField
from .base import BaseDoc
from .laboratory import Laboratory

class Patient(BaseDoc):
    lab = ReferenceField(Laboratory, required=True)
    name = StringField(required=True, max_length=200)
    birthdate = DateField()
    email = StringField()
    phone = StringField()
    notes = StringField()
