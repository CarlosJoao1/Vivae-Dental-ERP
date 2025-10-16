# backend/app.py
from flask import Flask, jsonify, request
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
from flask import redirect

def create_app():
    app = Flask(__name__)

    # Basic config
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret")
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret")
    app.config["JSON_SORT_KEYS"] = False

    # ---- CORS (dinâmico por env) ----
    # Define no Render (backend): FRONTEND_ORIGINS="https://<frontend>.onrender.com,http://localhost:5173,http://0.0.0.0:5173"
    try:
        from flask_cors import CORS

        raw_origins = os.getenv(
            "FRONTEND_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173,http://0.0.0.0:5173"
        )
        origins = [o.strip() for o in raw_origins.split(",") if o.strip()]

        CORS(
            app,
            resources={r"/*": {"origins": origins}},
            supports_credentials=True,
            allow_headers=["Content-Type", "Authorization"],
            expose_headers=["Authorization"],
            methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
            max_age=86400,
        )
    except Exception as e:
        app.logger.warning(f"CORS setup failed: {e}")

    # Respeitar cabeçalhos X-Forwarded-* atrás do proxy
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

    # Init subsystems
    init_db(app)
    init_auth(app)

    # Blueprints
    register_blueprints(app)

    # Log incoming requests
    @app.before_request
    def log_request():
        app.logger.info(f"[REQUEST] {request.method} {request.path} from {request.remote_addr} Origin: {request.headers.get('Origin', 'None')}")

    # Ensure CORS headers are always present (backup for preflight OPTIONS)
    @app.after_request
    def after_request(response):
        origin = request.headers.get('Origin')
        raw_origins = os.getenv(
            "FRONTEND_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173,http://0.0.0.0:5173"
        )
        allowed_origins = [o.strip() for o in raw_origins.split(",") if o.strip()]
        
        if origin in allowed_origins:
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            response.headers['Access-Control-Expose-Headers'] = 'Authorization'
        
        app.logger.info(f"[RESPONSE] {response.status_code} for {request.path}")
        return response

    # Errors
    @app.errorhandler(404)
    def _nf(e):
        # If non-API path was requested on the backend host, redirect to frontend homepage
        try:
            path = request.path or ""
            if not path.startswith("/api"):
                raw_origins = os.getenv(
                    "FRONTEND_ORIGINS",
                    "http://localhost:5173,http://127.0.0.1:5173,http://0.0.0.0:5173"
                )
                origins = [o.strip() for o in raw_origins.split(",") if o.strip()]
                if origins:
                    return redirect(origins[0], code=302)
        except Exception:
            pass
        return jsonify({"error": "not found"}), 404

    @app.errorhandler(500)
    def _ise(e):
        app.logger.exception("Unhandled 500")
        return jsonify({"error": "internal server error"}), 500

    # Production guard: require proper secrets in production-like envs
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
            # If JWT secret is missing, fallback to SECRET_KEY to avoid downtime, but warn loudly
            if app.config.get("JWT_SECRET_KEY") == "dev-jwt-secret" or not os.getenv("JWT_SECRET_KEY"):
                app.logger.warning("JWT_SECRET_KEY not set in production; falling back to SECRET_KEY (set JWT_SECRET_KEY ASAP)")
                app.config["JWT_SECRET_KEY"] = app.config["SECRET_KEY"]
    except Exception as e:
        app.logger.error("Production secrets validation failed: %s", e)
        # Falhar o arranque em produção para segurança
        raise

    # Seed (idempotent)
    with app.app_context():
        run_seed()

    return app


app = create_app()

if __name__ == "__main__":
    # Em dev
    app.run(host="0.0.0.0", port=5000, debug=True)
