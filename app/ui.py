"""User-facing web interface routes."""

from flask import Blueprint, redirect, render_template, url_for

ui_bp = Blueprint("ui", __name__)


@ui_bp.get("/")
def index():
    """Send visitors to the login page."""
    return redirect(url_for("ui.login_page"))


@ui_bp.get("/login")
def login_page():
    """Render the login page."""
    return render_template("login.html")


@ui_bp.get("/register")
def register_page():
    """Render the account registration page."""
    return render_template("register.html")


@ui_bp.get("/forgot-password")
def forgot_password_page():
    """Render the password-reset request page."""
    return render_template("forgot_password.html")


@ui_bp.get("/reset-password")
def reset_password_page():
    """Render the password-reset completion page."""
    return render_template("reset_password.html")


@ui_bp.get("/dashboard")
def dashboard_router():
    """Render the dashboard shell while the browser resolves the role."""
    return render_template("dashboard.html", expected_role="")


@ui_bp.get("/admin")
def admin_dashboard():
    """Render the Admin dashboard."""
    return render_template("dashboard.html", expected_role="Admin")


@ui_bp.get("/manager")
def manager_dashboard():
    """Render the Manager dashboard."""
    return render_template("dashboard.html", expected_role="Manager")


@ui_bp.get("/accountant")
def accountant_dashboard():
    """Render the Accountant dashboard."""
    return render_template("dashboard.html", expected_role="Accountant")


@ui_bp.get("/employee")
def employee_dashboard():
    """Render the Employee dashboard."""
    return render_template("dashboard.html", expected_role="Employee")
