from mongoengine import StringField, ReferenceField
from .base import BaseDoc
from .laboratory import Laboratory


class ShippingAddress(BaseDoc):
    meta = {
        'auto_create_index': False,
        'indexes': [
            {'fields': ['lab', 'code'], 'unique': True},
        ]
    }

    lab = ReferenceField(Laboratory, required=True)

    code = StringField(required=True, max_length=50)
    address1 = StringField()
    address2 = StringField()
    postal_code = StringField()
    city = StringField()
    country_code = StringField(max_length=3)  # references Country.code
