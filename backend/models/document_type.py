from mongoengine import StringField, ReferenceField
from .base import BaseDoc
from .laboratory import Laboratory

class DocumentType(BaseDoc):
    lab = ReferenceField(Laboratory, required=True)
    name = StringField(required=True, max_length=120)
    extension = StringField()
