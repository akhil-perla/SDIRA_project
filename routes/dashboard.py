import json
import os
from flask import Blueprint, render_template, session, redirect, url_for, flash

dashboard_bp = Blueprint('dashboard', __name__)

FILES_JSON_PATH = "data/files.json"  # Update the path if necessary

@dashboard_bp.route('/')
def dashboard():
    if 'user' not in session:
        flash('You must be logged in to view the dashboard.', 'danger')
        return redirect(url_for('auth.login'))

    username = session['user']

    # Load the uploaded files from JSON
    files = []
    if os.path.exists(FILES_JSON_PATH):
        with open(FILES_JSON_PATH, "r") as file:
            try:
                all_files = json.load(file)
                # Filter files uploaded by the logged-in user
                files = [f for f in all_files if f.get("issuer") == username]
            except json.JSONDecodeError:
                files = []  # In case of JSON format issues

    return render_template('dashboard.html', username=username, files=files)


