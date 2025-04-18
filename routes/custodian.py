import os
import json
from flask import Blueprint, render_template, session, redirect, url_for, flash, request

custodian_bp = Blueprint("custodian", __name__)

FILES_JSON_PATH = "storage/files.json"
USER_FILE = "storage/users.json"

@custodian_bp.route('/dashboard')
def dashboard():
    if 'user' not in session or session.get('role') != 'custodian':
        flash('You must be logged in as a custodian to view this page.', 'danger')
        return redirect(url_for('auth.login'))

    username = session['user']
    
    # Load issuers data
    with open('storage/issuers.json', 'r') as f:
        issuers_data = json.load(f)
    
    # Filter issuers for this custodian
    associated_issuers = []
    for issuer_name, issuer_info in issuers_data.items():
        if issuer_info.get('custodian') == username:
            associated_issuers.append(issuer_name)

    return render_template('custodian_dashboard.html', 
                         username=username,
                         custodian=username,
                         issuers=associated_issuers)


@custodian_bp.route('/add_issuer', methods=['POST'])
def add_issuer():
    if 'user' not in session or session.get('role') != 'custodian':
        flash("Unauthorized access.", "danger")
        return redirect(url_for("auth.login"))

    custodian = session['user']
    new_issuer = request.form.get("issuer", "").strip()

    if not new_issuer:
        flash("Issuer username is required.", "warning")
        return redirect(url_for("custodian.dashboard"))

    # Load users
    USER_FILE = "storage/users.json"
    if not os.path.exists(USER_FILE):
        flash("User database not found.", "danger")
        return redirect(url_for("custodian.dashboard"))

    with open(USER_FILE, "r") as f:
        users = json.load(f)

    # Validate issuer
    if new_issuer not in users or users[new_issuer].get("role") != "issuer":
        flash("Invalid issuer username.", "danger")
        return redirect(url_for("custodian.dashboard"))

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

    return redirect(url_for("custodian.dashboard"))

