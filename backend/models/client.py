from mongoengine import StringField, BooleanField, ReferenceField, DictField, ListField, DateField
from .base import BaseDoc
from .laboratory import Laboratory
from .currency import Currency
from .payment_type import PaymentType
from .payment_form import PaymentForm
from .payment_method import PaymentMethod

class Client(BaseDoc):
    meta = {
        'auto_create_index': False,  # avoid auto ensure_indexes at startup
        'indexes': [
            {'fields': ['lab', 'tax_id'], 'unique': True, 'sparse': True},
            {'fields': ['lab', 'email'], 'unique': True, 'sparse': True},
            {'fields': ['lab', 'code'], 'unique': True},
        ]
    }

    lab = ReferenceField(Laboratory, required=True)

    # Identificação
    code = StringField(required=True, max_length=50)
    name = StringField(required=True, max_length=200)
    first_name = StringField()
    last_name = StringField()
    gender = StringField(choices=("male","female","other"))
    birthdate = DateField()

    # Contactos
    email = StringField()
    phone = StringField()
    address = StringField()

    # Faturação
    type = StringField(choices=("clinic","dentist","other"), default="clinic")
    tax_id = StringField()
    billing_address = DictField()  # {street, city, postal_code, country}
    shipping_address = DictField()
    payment_terms = StringField()  # e.g., NET30

    notes = StringField()
    active = BooleanField(default=True)

    contacts = ListField(DictField())  # [{name, role, email, phone}]

    # Preferências financeiras
    preferred_currency = ReferenceField(Currency, required=False)
    payment_type = ReferenceField(PaymentType, required=False)
    payment_form = ReferenceField(PaymentForm, required=False)
    payment_method = ReferenceField(PaymentMethod, required=False)
