import os
import json
from flask import Flask, session, request, g
from werkzeug.middleware.proxy_fix import ProxyFix
from flask import redirect, url_for
from routes.recharge import recharge_bp
from routes.payment import payment_bp
from routes.auth import auth_bp
from routes.i18n import bp as i18n_bp
from routes.account import account_bp


# ---------------------------
# App Factory
# ---------------------------
def create_app() -> Flask:
    app = Flask(__name__)

    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

    app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-change-me")  # prod: env only
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["PREFERRED_URL_SCHEME"] = os.getenv("PREFERRED_URL_SCHEME", "https")

    # ---------------------------
    # I18n (JSON l10n)
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
        # session > query param > header > fr
        lang = session.get("lang")
        if not lang:
            lang = request.args.get("lang")
        if not lang:
            accept = request.headers.get("Accept-Language", "")
            lang = "fr" if accept.lower().startswith("fr") else "en"

        session["lang"] = lang if lang in ("fr", "en") else "fr"
        g.lang = session["lang"]
        g.l10n = _load_l10n(g.lang)

    def t(key: str, default: str = "") -> str:
        # Dot keys: "recharge.enterNumber.title"
        cur = g.get("l10n", {})
        for part in key.split("."):
            if not isinstance(cur, dict) or part not in cur:
                return default
            cur = cur[part]
        return cur if isinstance(cur, str) else default

    app.jinja_env.globals["t"] = t

    # ---------------------------
    # Blueprints
    # ---------------------------
    app.register_blueprint(recharge_bp)
    app.register_blueprint(payment_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(i18n_bp)
    app.register_blueprint(account_bp)
    return app
    

app = create_app()
@app.route("/")
def index():
    return redirect(url_for("recharge.enter_number_get"))
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8080")), debug=True)