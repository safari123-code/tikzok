# ---------------------------
# Admin Routes — FINAL PRO CLEAN
# ---------------------------

from functools import wraps
from flask import Blueprint, render_template, redirect, session, url_for, request

import config
from services.admin.admin_service import AdminService
from services.order.history_service import HistoryService
from services.core.utils import mask_phone

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


# ---------------------------
# Admin auth helpers
# ---------------------------
def _current_user_email() -> str:
    return (session.get("user_email") or "").strip().lower()


def _is_admin():
    email = _current_user_email()

    is_admin = email in config.ADMIN_EMAILS
    is_super = email == config.SUPER_ADMIN_EMAIL

    session["is_admin"] = is_admin
    session["is_super_admin"] = is_super

    return is_admin


def admin_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):

        if not session.get("user_id"):
            return redirect(url_for("auth.login"))

        if not _is_admin():
            return redirect(url_for("recharge.enter_number_get"))

        return view_func(*args, **kwargs)

    return wrapped


# ---------------------------
# Shared context
# ---------------------------
def _shared_context() -> dict:
    return {
        "history_count": HistoryService.count_all(),
    }


# ---------------------------
# Dashboard
# ---------------------------
@admin_bp.get("/")
@admin_required
def dashboard_get():

    dashboard = AdminService.get_dashboard_data()
    stats = AdminService.get_dashboard_stats()

    return render_template(
        "admin/dashboard.html",
        dashboard=dashboard,
        stats=stats,
        recent_recharges=dashboard.get("recent_recharges", []),
        **_shared_context(),
    )


# ---------------------------
# Users
# ---------------------------
@admin_bp.get("/users")
@admin_required
def users_get():

    query = (request.args.get("q") or "").strip()

    users = (
        AdminService.search_users(query)
        if query
        else AdminService.get_users()
    )

    return render_template(
        "admin/users.html",
        users=users,
        users_count=len(users),
        query=query,
        **_shared_context(),
    )


# ---------------------------
# User detail
# ---------------------------
@admin_bp.get("/user/<user_id>")
@admin_required
def user_detail_get(user_id):

    if not user_id:
        return redirect(url_for("admin.users_get"))

    data = AdminService.get_user_full_detail(user_id)

    items = [
        {
            **i,
            "phone": mask_phone(
                i.get("phone"),
                session.get("is_super_admin", False)
            )
        }
        for i in data.get("history", [])
    ]

    return render_template(
        "admin/user_detail.html",
        user=data.get("user"),
        items=items,
        total=data.get("total_amount", 0),
        count=data.get("count", 0),
        countries=data.get("countries", []),
        cards=data.get("cards", []),
        **_shared_context(),
    )


# ---------------------------
# Recharges
# ---------------------------
@admin_bp.get("/recharges")
@admin_required
def recharges_get():

    recharges = AdminService.get_recharges()

    return render_template(
        "admin/recharges.html",
        recharges=recharges,
        recharges_count=len(recharges),
        **_shared_context(),
    )


# ---------------------------
# Transactions
# ---------------------------
@admin_bp.get("/transactions")
@admin_required
def transactions_get():

    transactions = AdminService.get_transactions()

    return render_template(
        "admin/transactions.html",
        transactions=transactions,
        transactions_count=len(transactions),
        **_shared_context(),
    )