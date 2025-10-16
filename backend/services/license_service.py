# backend/services/license_service.py
import json, os
from functools import wraps
from flask import abort, current_app

class LicenseService:
    def __init__(self, app):
        self.features = {}
        # Resolve caminho do ficheiro de licença: permite /app em container ou raiz do projeto em dev
        candidate = app.config.get("LICENSE_FILE")
        if not candidate:
            # prefer /app/license.json (container), fallback ../license.json (repo root)
            p1 = "/app/license.json"
            p2 = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "license.json"))
            candidate = p1 if os.path.exists(p1) else p2
        self.load(candidate)

    def load(self, path):
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.features = data.get("features", {})
        else:
            self.features = {}

    def require(self, feature):
        # uso interno direto (em runtime, dentro de contexto)
        if not self.features.get(feature, False):
            abort(403)

def require_feature(feature: str):
    """
    Decorator seguro: verifica a licença *durante* a request,
    quando o contexto Flask (current_app) já existe.
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            current_app.license.require(feature)
            return fn(*args, **kwargs)
        return wrapper
    return decorator
