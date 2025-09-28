# backend/app.py
from flask import Flask, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix
import os

from config.db import init_db
from config.auth import init_auth, jwt  # noqa
from routes import register_blueprints
from core.seed import run_seed

def create_app():
    app = Flask(__name__)

    # Basic config
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret")
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret")
    app.config["JSON_SORT_KEYS"] = False

    # CORS
    try:
        from flask_cors import CORS
        CORS(
            app,
            resources={r"/api/*": {"origins": [
                "http://localhost:5173",
                "http://127.0.0.1:5173",
                "http://0.0.0.0:5173"
            ]}},
            supports_credentials=True,
            expose_headers=["Authorization"],
        )
    except Exception:
        pass

    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

    # Init subsystems
    init_db(app)
    init_auth(app)

    # Blueprints
    register_blueprints(app)

    # Errors
    @app.errorhandler(404)
    def _nf(e): return jsonify({"error": "not found"}), 404

    @app.errorhandler(500)
    def _ise(e):
        app.logger.exception("Unhandled 500")
        return jsonify({"error": "internal server error"}), 500

    # Seed (idempotent)
    with app.app_context():
        run_seed()

    return app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
