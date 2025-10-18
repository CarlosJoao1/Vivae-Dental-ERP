import os

class Settings:
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/vivae_dental_erp")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret")
    ACCESS_TOKEN_EXPIRES_MIN = int(os.getenv("ACCESS_TOKEN_EXPIRES_MIN", "15"))
    REFRESH_TOKEN_EXPIRES_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRES_DAYS", "7"))
    DEFAULT_LANG = os.getenv("DEFAULT_LANG", "pt")
