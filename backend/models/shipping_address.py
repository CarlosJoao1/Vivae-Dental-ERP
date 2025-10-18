from mongoengine import StringField, ReferenceField
from .base import BaseDoc
from .laboratory import Laboratory
from .client import Client


class ShippingAddress(BaseDoc):
    meta = {
        'auto_create_index': False,
        'indexes': [
            # Unique per lab+client+code for new data; sparse allows legacy docs without client
            {'fields': ['lab', 'client', 'code'], 'unique': True, 'sparse': True},
            # Non-unique index to support queries by lab and client efficiently
            {'fields': ['lab', 'client']},
        ]
    }

    lab = ReferenceField(Laboratory, required=True)
    # Shipping addresses are associated to a specific client (legacy docs may lack this)
    client = ReferenceField(Client, required=False)

    code = StringField(required=True, max_length=50)
    address1 = StringField()
    address2 = StringField()
    postal_code = StringField()
    city = StringField()
    country_code = StringField(max_length=3)  # references Country.code
