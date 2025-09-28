# backend/routes/__init__.py
from flask import Flask

def register_blueprints(app: Flask):
    from .health import bp as health_bp
    app.register_blueprint(health_bp)

    # Auth
    try:
        from .auth import bp as auth_bp
        app.register_blueprint(auth_bp)
    except Exception as e:
        app.logger.warning("auth not registered: %s", e)

    # Masterdata (patients, technicians, services, doctypes, labs)
    try:
        from .masterdata import bp as master_bp
        app.register_blueprint(master_bp)
    except Exception as e:
        app.logger.warning("masterdata not registered: %s", e)

    # Tenants alias
    try:
        from .tenants import bp as tenants_bp
        app.register_blueprint(tenants_bp)
    except Exception as e:
        app.logger.warning("tenants not registered: %s", e)
