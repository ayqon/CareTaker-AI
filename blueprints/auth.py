from functools import wraps
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from models import User, db

auth_bp = Blueprint("auth", __name__)


def role_required(role):
    """Decorator that enforces login + role check. Returns 403 if role mismatches."""
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if current_user.role != role:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


@auth_bp.route("/", methods=["GET", "POST"])
def index():
    if current_user.is_authenticated:
        return redirect(
            url_for("worker.worker_dashboard" if current_user.role == "worker" else "supervisor.supervisor_dashboard")
        )

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()
        if user is None or not user.check_password(password):
            flash("Invalid username or password.", "error")
            return redirect(url_for("auth.index"))

        login_user(user)
        return redirect(
            url_for("worker.worker_dashboard" if user.role == "worker" else "supervisor.supervisor_dashboard")
        )

    return render_template("index.html")


@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(
            url_for("worker.worker_dashboard" if current_user.role == "worker" else "supervisor.supervisor_dashboard")
        )

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "")
        preferred_language = request.form.get("preferred_language", "en")
        age = request.form.get("age", "")
        gender = request.form.get("gender", "")

        if not username or not password:
            flash("Username and password are required.", "error")
            return redirect(url_for("auth.signup"))

        if role not in ("worker", "supervisor"):
            flash("Please select a valid role.", "error")
            return redirect(url_for("auth.signup"))

        if User.query.filter_by(username=username).first():
            flash("Username already taken.", "error")
            return redirect(url_for("auth.signup"))

        user = User(
            username=username,
            role=role,
            preferred_language=preferred_language,
            age=int(age) if age else None,
            gender=gender if gender else None,
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        login_user(user)
        return redirect(
            url_for("worker.worker_dashboard" if role == "worker" else "supervisor.supervisor_dashboard")
        )

    return render_template("signup.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.index"))
