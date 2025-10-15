from mongoengine import StringField, BooleanField, ReferenceField
from .base import BaseDoc
from .laboratory import Laboratory

class PaymentMethod(BaseDoc):
    lab = ReferenceField(Laboratory, required=True)
    code = StringField()
    name = StringField(required=True)
    active = BooleanField(default=True)
