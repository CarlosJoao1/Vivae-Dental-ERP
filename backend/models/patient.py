from mongoengine import StringField, DateField, ReferenceField
from .base import BaseDoc
from .laboratory import Laboratory

class Patient(BaseDoc):
    lab = ReferenceField(Laboratory, required=True)

    # Identificação
    name = StringField(required=True, max_length=200)
    first_name = StringField()
    last_name = StringField()
    gender = StringField(choices=("male","female","other"))
    birthdate = DateField()

    # Contacto
    email = StringField()
    phone = StringField()
    address = StringField()

    notes = StringField()
