# backend/config/auth.py
from flask_jwt_extended import JWTManager
from datetime import timedelta

jwt = JWTManager()

def init_auth(app):
    # Expirações robustas
    app.config.setdefault("JWT_ACCESS_TOKEN_EXPIRES", timedelta(minutes=30))
    app.config.setdefault("JWT_REFRESH_TOKEN_EXPIRES", timedelta(days=7))
    jwt.init_app(app)
