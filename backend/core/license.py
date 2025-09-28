# backend/core/license.py
# Simple placeholder for feature licensing system.
# You can expand this to read features from DB or environment and
# create decorators to protect endpoints per feature.
class LicenseManager:
    def __init__(self, features=None):
        self.features = set(features or [])

    def has(self, feature: str) -> bool:
        return feature in self.features

    def require(self, feature: str):
        def deco(fn):
            def wrapper(*args, **kwargs):
                if not self.has(feature):
                    from flask import jsonify
                    return jsonify({"error": "feature not licensed", "feature": feature}), 403
                return fn(*args, **kwargs)
            # keep attributes
            wrapper.__name__ = fn.__name__
            return wrapper
        return deco
