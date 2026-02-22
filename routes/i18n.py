# ---------------------------
# I18n routes
# ---------------------------

from flask import Blueprint, session, redirect, request, url_for, render_template
from urllib.parse import urlparse

bp = Blueprint("i18n", __name__)

ALLOWED_LANGS = {"fr", "en"}


def _safe_next(next_url: str | None) -> str:
    # Empêche open redirect : on n'accepte que des chemins internes
    if not next_url:
        return url_for("recharge.enter_number_get")
    parsed = urlparse(next_url)
    if parsed.scheme or parsed.netloc:
        return url_for("recharge.enter_number_get")
    if not next_url.startswith("/"):
        return url_for("recharge.enter_number_get")
    return next_url


@bp.route("/language")
def language_get():
    next_url = _safe_next(request.args.get("next"))
    current_lang = session.get("lang", "fr")
    return render_template(
        "account/language.html",
        current_lang=current_lang,
        next_url=next_url,
        allowed_langs=sorted(ALLOWED_LANGS),
    )


@bp.route("/change-lang/<lang>")
def change_lang(lang: str):
    if lang not in ALLOWED_LANGS:
        lang = "fr"
    session["lang"] = lang
    return redirect(_safe_next(request.args.get("next")))