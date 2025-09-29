# backend/routes/__init__.py
from flask import current_app

def register_blueprints(app):
    """
    Regista explicitamente os blueprints. Se algum falhar a importar,
    escreve um aviso nos logs mas não impede o arranque da app.
    """
    # 1) /api/health (se existir)
    try:
        from .health import bp as health_bp  # type: ignore
        app.register_blueprint(health_bp)
        app.logger.info("✔ registered blueprint: health -> %s", getattr(health_bp, "url_prefix", "/api"))
    except Exception as e:
        app.logger.warning("health not registered: %s", e)

    # 2) /api/auth  (login/refresh/me)
    try:
        from .auth import bp as auth_bp  # type: ignore
        app.register_blueprint(auth_bp)
        app.logger.info("✔ registered blueprint: auth -> %s", getattr(auth_bp, "url_prefix", "/api/auth"))
    except Exception as e:
        # Este log aparece nos teus logs Render. Se vires aqui erro,
        # o módulo routes.auth ainda está a falhar ao importar.
        app.logger.warning("auth not registered: %s", e)

    # (Opcional) se tiveres outros ficheiros de rotas, regista-os aqui da mesma forma:
    # try:
    #     from .patients import bp as patients_bp
    #     app.register_blueprint(patients_bp)
    #     app.logger.info("✔ registered blueprint: patients -> %s", patients_bp.url_prefix)
    # except Exception as e:
    #     app.logger.warning("patients not registered: %s", e)
