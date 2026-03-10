# ---------------------------
# routes/history.py
# ---------------------------

from flask import Blueprint, render_template
from services.history_service import HistoryService

history_bp = Blueprint("history", __name__, url_prefix="/history")


# ---------------------------
# History index
# ---------------------------
@history_bp.get("/")
def index_get():
    history_items = HistoryService.get_all()
    history_count = HistoryService.count()

    return render_template(
        "history/index.html",
        items=history_items,
        history_count=history_count,
    )