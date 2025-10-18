from mongoengine import StringField, ReferenceField, IntField, FloatField, DateField
from .base import BaseDoc
from .laboratory import Laboratory
from .client import Client


class ClientPrice(BaseDoc):
    meta = {
        'auto_create_index': False,
        'indexes': [
            {'fields': ['lab', 'client']},
        ]
    }

    lab = ReferenceField(Laboratory, required=True)
    client = ReferenceField(Client, required=True)

    sale_type = StringField()          # Tipo de Venda
    sale_code = StringField()          # Código Venda
    code = StringField()               # Código (ex: serviço/produto)
    uom = StringField()                # Unidade Medida
    min_qty = IntField(default=1)      # Quantidade Mínima
    unit_price = FloatField()          # Preço Unitário
    start_date = DateField()           # Data Início
    end_date = DateField()             # Data Fim
