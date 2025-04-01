import os
import json
from flask import Blueprint, render_template, session, redirect, url_for, flash, request

custodian_bp = Blueprint("custodian", __name__)

FILES_JSON_PATH = "storage/files.json"
USER_FILE = "storage/users.json"

@custodian_bp.route('/dashboard')
def custodian_dashboard():
    if 'user' not in session or session.get('role') != 'custodian':
        flash("Unauthorized access.", "danger")
        return redirect(url_for("auth.login"))

    custodian = session['user']
    
    # Load associated issuers
    issuers = []
    users = {}
    if os.path.exists(USER_FILE):
        with open(USER_FILE, "r") as f:
            try:
                users = json.load(f)
                issuers = users.get(custodian, {}).get("manages", [])
            except json.JSONDecodeError:
                flash("Failed to load user data", "danger")
    
    # Load metadata and filter relevant files
    files = []
    if os.path.exists(FILES_JSON_PATH):
        with open(FILES_JSON_PATH, "r") as f:
            try:
                all_files = json.load(f)
                for file in all_files:
                    if (
                        file.get("issuer") in issuers and
                        custodian in file.get("custodians", [])
                    ):
                        files.append(file)
            except json.JSONDecodeError:
                flash("Failed to load file metadata", "danger")

    return render_template(
    "custodian_dashboard.html",
    custodian=custodian,
    files=files,
    issuers=issuers
    )


@custodian_bp.route('/add_issuer', methods=['POST'])
def add_issuer():
    if 'user' not in session or session.get('role') != 'custodian':
        flash("Unauthorized access.", "danger")
        return redirect(url_for("auth.login"))

    custodian = session['user']
    new_issuer = request.form.get("issuer", "").strip()

    if not new_issuer:
        flash("Issuer username is required.", "warning")
        return redirect(url_for("custodian.custodian_dashboard"))

    # Load users
    USER_FILE = "storage/users.json"
    if not os.path.exists(USER_FILE):
        flash("User database not found.", "danger")
        return redirect(url_for("custodian.custodian_dashboard"))

    with open(USER_FILE, "r") as f:
        users = json.load(f)

    # Validate issuer
    if new_issuer not in users or users[new_issuer].get("role") != "issuer":
        flash("Invalid issuer username.", "danger")
        return redirect(url_for("custodian.custodian_dashboard"))

    # Add issuer to custodian's 'manages' list
    manages = users[custodian].get("manages", [])
    if new_issuer in manages:
        flash("Issuer already associated with you.", "info")
    else:
        manages.append(new_issuer)
        users[custodian]["manages"] = manages
        with open(USER_FILE, "w") as f:
            json.dump(users, f, indent=4)
        flash(f"Issuer '{new_issuer}' added successfully!", "success")

    return redirect(url_for("custodian.custodian_dashboard"))

