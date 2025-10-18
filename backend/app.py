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
        # Extra patterns (e.g., wildcard) that we might accept at runtime
        raw_extra = os.getenv("FRONTEND_ORIGINS_EXTRA", "")
        origins = [o.strip() for o in raw_origins.split(",") if o.strip()]
        extra_origins = [o.strip() for o in raw_extra.split(",") if o.strip()]

        # Base CORS registration uses the explicit origins list (exact matches)
        CORS(
            app,
            resources={r"/*": {"origins": origins}},
            supports_credentials=True,
            # Include custom tenant header to allow cross-origin requests with X-Tenant-Id
            allow_headers=["Content-Type", "Authorization", "X-Tenant-Id"],
            expose_headers=["Authorization"],
            methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
            max_age=86400,
        )
        # Keep a cached set of allowed origins and wildcard patterns for after_request
        app.config["_ALLOWED_ORIGINS"] = set(origins)
        app.config["_ALLOWED_ORIGINS_PATTERNS"] = extra_origins
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
        import re
        origin = request.headers.get('Origin')

        # Exact list from env at startup
        allowed_list = app.config.get("_ALLOWED_ORIGINS") or set()
        # Optional wildcard patterns (e.g., https://vivae-dental-erp-*.onrender.com)
        pattern_list = app.config.get("_ALLOWED_ORIGINS_PATTERNS") or []

        def _match_origin(o: str) -> bool:
            if o in allowed_list:
                return True
            for pat in pattern_list:
                try:
                    # convert simple glob to regex
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
            # Mirror allow headers here as a fallback for preflight requests
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Tenant-Id'
            response.headers['Access-Control-Expose-Headers'] = 'Authorization'

        app.logger.info(f"[RESPONSE] {response.status_code} for {request.path}")
        return response

    # Errors
    @app.errorhandler(404)
    def _nf(e):
        # If non-API path was requested on the backend host, redirect to frontend preserving path
        try:
            path = request.path or ""
            if not path.startswith("/api"):
                raw_origins = os.getenv(
                    "FRONTEND_ORIGINS",
                    "http://localhost:5173,http://127.0.0.1:5173,http://0.0.0.0:5173"
                )
                origins = [o.strip() for o in raw_origins.split(",") if o.strip()]
                if origins:
                    # Prefer a non-localhost origin if available (avoid redirecting to localhost in prod)
                    def _is_local(u: str) -> bool:
                        return any(h in u for h in ("localhost", "127.0.0.1", "0.0.0.0"))

                    preferred = next((o for o in origins if not _is_local(o)), None) or origins[0]
                    base = preferred.rstrip("/")
                    # Preserve the requested path and query string for SPA routing
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
