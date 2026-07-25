"""Serves the static admin console page. Not part of the JSON API."""

from flask import Blueprint, render_template

admin_ui_bp = Blueprint("admin_ui", __name__)


@admin_ui_bp.get("/admin")
def admin_dashboard():
    return render_template("admin.html")

@admin_ui_bp.get("/accountant")
def accountant_dashboard():
    return render_template("accountant.html")


@admin_ui_bp.get("/employee")
def employee_dashboard():
    return render_template("employee.html")


@admin_ui_bp.get("/manager")
def manager_dashboard():
    return render_template("manager.html")

