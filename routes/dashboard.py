from flask import Blueprint, render_template, jsonify
import json

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")

@dashboard_bp.route("/")
def dashboard():
    try:
        with open("storage/files.json", "r") as f:
            files = json.load(f)
    except FileNotFoundError:
        files = []

    return render_template("dashboard.html", files=files)
