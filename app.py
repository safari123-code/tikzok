# ---------------------------
# Tikzok - Application Entry
# ---------------------------
import os
import json
from datetime import datetime

from flask import Flask, session, request, g, redirect, url_for
from werkzeug.middleware.proxy_fix import ProxyFix



import config

from routes.recharge import recharge_bp
from routes.payment import payment_bp
from routes.auth import auth_bp
from routes.i18n import bp as i18n_bp
from routes.account import account_bp
from routes.history import history_bp


# ---------------------------
# App Factory
# ---------------------------
def create_app() -> Flask:

    app = Flask(__name__)

    # Proxy (Google Cloud / reverse proxy safe)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

    # ---------------------------
    # Security Config
    # ---------------------------
    app.secret_key = config.SECRET_KEY or os.getenv("FLASK_SECRET_KEY")

    if not app.secret_key:
        raise RuntimeError("SECRET_KEY must be set")

    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_SECURE"] = os.getenv("ENV") == "production"
    app.config["PREFERRED_URL_SCHEME"] = os.getenv("PREFERRED_URL_SCHEME", "https")

    # ---------------------------
    # Inject current time
    # ---------------------------
    @app.context_processor
    def inject_now():
        return dict(now=datetime.now)

    # ---------------------------
    # I18n (JSON based)
    # ---------------------------
    def _load_l10n(lang: str) -> dict:

        lang = (lang or "fr").lower()

        if lang not in ("fr", "en"):
            lang = "fr"

        path = os.path.join(os.path.dirname(__file__), "l10n", f"{lang}.json")

        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    @app.before_request
    def _set_lang():

        lang = session.get("lang")

        if not lang:
            lang = request.args.get("lang")

        if not lang:
            accept = request.headers.get("Accept-Language", "").lower()
            lang = "fr" if accept.startswith("fr") else "en"

        if lang not in ("fr", "en"):
            lang = "fr"

        session["lang"] = lang
        g.lang = lang
        g.l10n = _load_l10n(lang)

    # ---------------------------
    # Translation helper
    # ---------------------------
    def t(key: str, params: dict | None = None, default: str = "") -> str:

        cur = g.get("l10n", {})

        for part in key.split("."):

            if not isinstance(cur, dict) or part not in cur:
                return default or key

            cur = cur[part]

        if not isinstance(cur, str):
            return default or key

        if params:
            for k, v in params.items():
                cur = cur.replace(f"{{{k}}}", str(v))

        return cur

    app.jinja_env.globals["t"] = t

    # ---------------------------
    # Blueprints
    # ---------------------------
    app.register_blueprint(recharge_bp)
    app.register_blueprint(payment_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(i18n_bp)
    app.register_blueprint(account_bp)
    app.register_blueprint(history_bp)

    return app


# ---------------------------
# App Init
# ---------------------------
app = create_app()


@app.route("/")
def index():
    return redirect(url_for("recharge.enter_number_get"))


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8080")),
        debug=os.getenv("ENV") != "production"
    )