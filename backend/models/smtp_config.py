from mongoengine import StringField, BooleanField, IntField, ReferenceField
from .base import BaseDoc
from .laboratory import Laboratory


class SmtpConfig(BaseDoc):
    lab = ReferenceField(Laboratory, required=True)
    server = StringField(required=True)
    port = IntField(default=587)
    use_tls = BooleanField(default=True)
    use_ssl = BooleanField(default=False)
    username = StringField()
    password = StringField()
    # sender will default to username; optional friendly name removed per requirements
