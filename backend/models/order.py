from mongoengine import StringField, ReferenceField, DateField, ListField, DictField, FloatField
from .base import BaseDoc
from .laboratory import Laboratory
from .client import Client

class Order(BaseDoc):
    lab = ReferenceField(Laboratory, required=True)
    number = StringField()
    date = DateField()
    client = ReferenceField(Client, required=True)
    client_code = StringField(required=True)
    currency = StringField(default="EUR")
    lines = ListField(DictField())  # [{description, qty, price, total}]
    total = FloatField(default=0.0)
