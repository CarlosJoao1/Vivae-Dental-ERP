# backend/app.py
from flask import Flask, jsonify, request, redirect
from werkzeug.middleware.proxy_fix import ProxyFix
import os
try:
    # Load .env for offline/dev environments
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass

from config.db import init_db
from config.auth import init_auth, jwt  # noqa
from routes import register_blueprints
from core.seed import run_seed


def setup_cors(app):
    """Configure CORS settings and handlers."""
    try:
        from flask_cors import CORS
        
        raw_origins = os.getenv(
            "FRONTEND_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173,http://0.0.0.0:5173"
        )
        raw_extra = os.getenv("FRONTEND_ORIGINS_EXTRA", "")
        origins = [o.strip() for o in raw_origins.split(",") if o.strip()]
        extra_origins = [o.strip() for o in raw_extra.split(",") if o.strip()]

        CORS(
            app,
            resources={r"/*": {"origins": origins}},
            supports_credentials=True,
            allow_headers=["Content-Type", "Authorization", "X-Tenant-Id"],
            expose_headers=["Authorization"],
            methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
            max_age=86400,
        )
        
        app.config["_ALLOWED_ORIGINS"] = set(origins)
        app.config["_ALLOWED_ORIGINS_PATTERNS"] = extra_origins
        
    except Exception as e:
        app.logger.warning(f"CORS setup failed: {e}")


def setup_cors_headers(app):
    """Setup after_request handler for CORS headers."""
    @app.after_request
    def after_request(response):
        import re
        origin = request.headers.get('Origin')

        allowed_list = app.config.get("_ALLOWED_ORIGINS") or set()
        pattern_list = app.config.get("_ALLOWED_ORIGINS_PATTERNS") or []

        def _match_origin(o: str) -> bool:
            if o in allowed_list:
                return True
            for pat in pattern_list:
                try:
                    rx = "^" + re.escape(pat).replace("\\*", ".*") + "$"
                    if re.match(rx, o or ""):
                        return True
                except Exception:
                    continue
            return False

        if origin and _match_origin(origin):
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Tenant-Id'
            response.headers['Access-Control-Expose-Headers'] = 'Authorization'

        app.logger.info(f"[RESPONSE] {response.status_code} for {request.path}")
        return response


def setup_error_handlers(app):
    """Configure error handlers and SPA fallback."""
    @app.errorhandler(404)
    def _nf(e):
        try:
            path = request.path or ""
            if not path.startswith("/api"):
                raw_origins = os.getenv(
                    "FRONTEND_ORIGINS",
                    "http://localhost:5173,http://127.0.0.1:5173,http://0.0.0.0:5173"
                )
                origins = [o.strip() for o in raw_origins.split(",") if o.strip()]
                if origins:
                    def _is_local(u: str) -> bool:
                        return any(h in u for h in ("localhost", "127.0.0.1", "0.0.0.0"))

                    preferred = next((o for o in origins if not _is_local(o)), None) or origins[0]
                    base = preferred.rstrip("/")
                    dest = f"{base}{path}"
                    if request.query_string:
                        dest = f"{dest}?{request.query_string.decode('utf-8', 'ignore')}"
                    try:
                        app.logger.info(f"[SPA-REDIRECT] 404 for {path} -> {dest}")
                    except Exception:
                        pass
                    return redirect(dest, code=302)
        except Exception:
            pass
        return jsonify({"error": "not found"}), 404

    @app.errorhandler(500)
    def _ise(e):
        app.logger.exception("Unhandled 500")
        return jsonify({"error": "internal server error"}), 500


def setup_request_logging(app):
    """Configure request logging."""
    @app.before_request
    def log_request():
        app.logger.info(f"[REQUEST] {request.method} {request.path} from {request.remote_addr} Origin: {request.headers.get('Origin', 'None')}")


def validate_production_secrets(app):
    """Validate required secrets in production environment."""
    try:
        env_lower = (os.getenv("ENV", "") or os.getenv("FLASK_ENV", "")).lower()
        is_prod = env_lower in ("prod", "production") or os.getenv("RENDER") == "true"
        if is_prod:
            app.logger.info(
                "[BOOT] Production mode detected. Secrets present -> SECRET_KEY=%s, JWT_SECRET_KEY=%s",
                bool(os.getenv("SECRET_KEY")), bool(os.getenv("JWT_SECRET_KEY"))
            )
            if app.config.get("SECRET_KEY") == "dev-secret" or not os.getenv("SECRET_KEY"):
                raise RuntimeError("SECRET_KEY must be set in production")
            if app.config.get("JWT_SECRET_KEY") == "dev-jwt-secret" or not os.getenv("JWT_SECRET_KEY"):
                app.logger.warning("JWT_SECRET_KEY not set in production; falling back to SECRET_KEY (set JWT_SECRET_KEY ASAP)")
                app.config["JWT_SECRET_KEY"] = app.config["SECRET_KEY"]
    except Exception as e:
        app.logger.error("Production secrets validation failed: %s", e)
        raise


def create_app():
    app = Flask(__name__)

    # Basic config
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret")
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret")
    app.config["JSON_SORT_KEYS"] = False

    # Respeitar cabeçalhos X-Forwarded-* atrás do proxy
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

    # Setup subsystems
    setup_cors(app)
    init_db(app)
    init_auth(app)
    register_blueprints(app)
    
    # Setup handlers and middleware
    setup_request_logging(app)
    setup_cors_headers(app)
    setup_error_handlers(app)
    
    # Production validation
    validate_production_secrets(app)

    # Seed (idempotent)
    with app.app_context():
        run_seed()

    return app


app = create_app()

if __name__ == "__main__":
    # Em dev
    app.run(host="0.0.0.0", port=5000, debug=True)
