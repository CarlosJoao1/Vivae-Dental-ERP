from mongoengine import StringField
from .base import BaseDoc


class Country(BaseDoc):
    meta = {
        'auto_create_index': False,
        'indexes': [
            {'fields': ['code'], 'unique': True},
        ]
    }

    # ISO-like code (e.g., PT, GB, ES)
    code = StringField(required=True, max_length=3)
    name = StringField(required=True, max_length=200)
