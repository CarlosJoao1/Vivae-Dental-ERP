from datetime import timedelta
from flask_jwt_extended import JWTManager

def init_jwt(app):
    app.config["JWT_SECRET_KEY"] = app.config["JWT_SECRET_KEY"]
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=app.config.get("ACCESS_TOKEN_EXPIRES_MIN", 15))
    app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=app.config.get("REFRESH_TOKEN_EXPIRES_DAYS", 7))
    JWTManager(app)
