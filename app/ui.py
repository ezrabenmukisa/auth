"""Serves the static admin console page. Not part of the JSON API."""

from flask import Blueprint, render_template

ui_bp = Blueprint("admin_ui", __name__)


@ui_bp.get("/admin")
def admin_dashboard():
    return render_template("admin.html")

@ui_bp.get("/accountant")
def accountant_dashboard():
    return render_template("accountant.html")


@ui_bp.get("/employee")
def employee_dashboard():
    return render_template("employee.html")


@ui_bp.get("/manager")
def manager_dashboard():
    return render_template("manager.html")

