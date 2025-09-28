from mongoengine import StringField, DecimalField, ReferenceField
from .base import BaseDoc
from .laboratory import Laboratory

class Service(BaseDoc):
    lab = ReferenceField(Laboratory, required=True)
    name = StringField(required=True, max_length=200)
    code = StringField()
    price = DecimalField(precision=2, default=0)
    description = StringField()
