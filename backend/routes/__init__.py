# backend/routes/__init__.py

def register_blueprints(app):
    """
    Regista explicitamente os blueprints. Se algum falhar a importar,
    escreve um aviso nos logs mas não impede o arranque da app.
    """
    # 1) /api/health
    try:
        from .health import bp as health_bp  # type: ignore
        app.register_blueprint(health_bp)
        app.logger.info("✔ registered blueprint: health -> %s",
                        getattr(health_bp, "url_prefix", "/api"))
    except Exception as e:
        app.logger.warning("health not registered: %s", e)

    # 2) /api/auth  (login/refresh/me)
    try:
        from .auth import bp as auth_bp  # type: ignore
        app.register_blueprint(auth_bp)
        app.logger.info("✔ registered blueprint: auth -> %s",
                        getattr(auth_bp, "url_prefix", "/api/auth"))
    except Exception as e:
        app.logger.warning("auth not registered: %s", e)

    # 3) /api/tenants  (lista de tenants para o dashboard)
    try:
        from .tenants import bp as tenants_bp  # type: ignore
        app.register_blueprint(tenants_bp)
        app.logger.info("✔ registered blueprint: tenants -> %s",
                        getattr(tenants_bp, "url_prefix", "/api/tenants"))
    except Exception as e:
        app.logger.warning("tenants not registered: %s", e)

    # 4) /api/masterdata  (CRUD básico de master data)
    try:
        from .masterdata import bp as masterdata_bp  # type: ignore
        app.register_blueprint(masterdata_bp)
        app.logger.info("✔ registered blueprint: masterdata -> %s",
                        getattr(masterdata_bp, "url_prefix", "/api/masterdata"))
    except Exception as e:
        app.logger.warning("masterdata not registered: %s", e)

    # 5) /api/sales  (orders/invoices)
    try:
        from .sales import bp as sales_bp  # type: ignore
        app.register_blueprint(sales_bp)
        app.logger.info("✔ registered blueprint: sales -> %s",
                        getattr(sales_bp, "url_prefix", "/api/sales"))
    except Exception as e:
        app.logger.warning("sales not registered: %s", e)

    # 6) /api/roles  (role features and policies)
    try:
        from .roles import bp as roles_bp  # type: ignore
        app.register_blueprint(roles_bp)
        app.logger.info("✔ registered blueprint: roles -> %s",
                        getattr(roles_bp, "url_prefix", "/api/roles"))
    except Exception as e:
        app.logger.warning("roles not registered: %s", e)

    # 7) /api/production/masterdata  (Production: UOM, Items, Locations, Suppliers)
    try:
        from .production.masterdata import bp as production_masterdata_bp  # type: ignore
        app.register_blueprint(production_masterdata_bp)
        app.logger.info("✔ registered blueprint: production_masterdata -> %s",
                        getattr(production_masterdata_bp, "url_prefix", "/api/production/masterdata"))
    except Exception as e:
        app.logger.warning("production_masterdata not registered: %s", e)

    # (exemplos para outros módulos)
    # try:
    #     from .patients import bp as patients_bp
    #     app.register_blueprint(patients_bp)
    #     app.logger.info("✔ registered blueprint: patients -> %s",
    #                     getattr(patients_bp, "url_prefix", "/api/patients"))
    # except Exception as e:
    #     app.logger.warning("patients not registered: %s", e)
