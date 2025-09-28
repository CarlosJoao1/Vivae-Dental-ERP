from mongoengine import Document, DateTimeField
from datetime import datetime

class BaseDoc(Document):
    meta = {"abstract": True}
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
