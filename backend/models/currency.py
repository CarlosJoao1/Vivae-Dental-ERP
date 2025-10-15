from mongoengine import StringField, BooleanField, ReferenceField
from .base import BaseDoc
from .laboratory import Laboratory

class Currency(BaseDoc):
    lab = ReferenceField(Laboratory, required=True)
    code = StringField(required=True, max_length=3)  # EUR, USD
    name = StringField()
    symbol = StringField()
    is_default = BooleanField(default=False)
    active = BooleanField(default=True)
