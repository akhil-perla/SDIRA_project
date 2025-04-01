import json
import os, mimetypes
from datetime import datetime
from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from werkzeug.utils import secure_filename

dashboard_bp = Blueprint('dashboard', __name__)

FILES_JSON_PATH = "storage/files.json"  # Update the path if necessary
USER_FILE = "storage/users.json" 
UPLOAD_FOLDER = "uploads"


# Constants
ALLOWED_EXTENSIONS = {"csv", "xlsx", "xls"}
os.makedirs("storage", exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Utilities
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_mime_type(filename):
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or "application/octet-stream"

def load_metadata():
    if not os.path.exists(FILES_JSON_PATH):
        return []
    try:
        with open(FILES_JSON_PATH, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []

def save_metadata(metadata):
    with open(FILES_JSON_PATH, "w") as f:
        json.dump(metadata, f, indent=4)

def load_users():
    if not os.path.exists(USER_FILE):
        return {}
    with open(USER_FILE, "r") as f:
        return json.load(f)

def file_exists(filename):
    return os.path.exists(os.path.join(UPLOAD_FOLDER, filename))

@dashboard_bp.route('/', methods=['GET', 'POST'])
def dashboard():
    if 'user' not in session or session.get('role') != 'issuer':
        flash('You must be logged in as an issuer to view this page.', 'danger')
        return redirect(url_for('auth.login'))

    username = session['user']
    users = load_users()

    # Handle File Upload (POST)
    if request.method == 'POST':
        if 'file' not in request.files:
            flash("No file part in request.", "danger")
            return redirect(url_for('dashboard.dashboard'))

        file = request.files['file']
        if file.filename == "":
            flash("No file selected.", "warning")
            return redirect(url_for('dashboard.dashboard'))

        if not allowed_file(file.filename):
            flash("Invalid file type. Allowed: .csv, .xlsx, .xls", "danger")
            return redirect(url_for('dashboard.dashboard'))

        filename = secure_filename(file.filename)
        if file_exists(filename):
            flash("File with this name already exists.", "warning")
            return redirect(url_for('dashboard.dashboard'))

        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        # Get selected custodians from form
        form_custodians = request.form.getlist("custodians")
        valid_custodians = users.get(username, {}).get("manages", [])

        # Validate selection
        invalid_custodians = [c for c in form_custodians if c not in valid_custodians]
        if invalid_custodians:
            flash(f"Invalid custodian(s): {', '.join(invalid_custodians)}", "danger")
            return redirect(url_for('dashboard.dashboard'))

        custodians = form_custodians

        # Build metadata
        file_metadata = {
            "filename": filename,
            "size": os.path.getsize(filepath),
            "upload_time": datetime.utcnow().isoformat(),
            "mime_type": get_mime_type(filename),
            "issuer": username,
            "custodians": custodians
        }

        metadata = load_metadata()
        metadata.append(file_metadata)
        save_metadata(metadata)

        flash("File uploaded successfully!", "success")
        return redirect(url_for('dashboard.dashboard'))

    # Load issuer files for dashboard
    files = []
    if os.path.exists(FILES_JSON_PATH):
        with open(FILES_JSON_PATH, "r") as f:
            try:
                all_files = json.load(f)
                files = [f for f in all_files if f.get("issuer") == username]
            except json.JSONDecodeError:
                files = []

    # Load manually associated custodians
    associated_custodians = users.get(username, {}).get("manages", [])

    return render_template(
        'dashboard.html',
        username=username,
        files=files,
        custodians=associated_custodians
    )



@dashboard_bp.route('/add_custodian', methods=['POST']) 
def add_custodian():
    if 'user' not in session or session.get('role') != 'issuer':
        flash("Unauthorized access", "danger")
        return redirect(url_for('auth.login'))

    issuer = session['user']
    new_custodian = request.form.get('custodian').strip()

    if not new_custodian:
        flash("Custodian username is required", "warning")
        return redirect(url_for('dashboard.dashboard'))

    # Load users
    if not os.path.exists(USER_FILE):
        flash("User database not found", "danger")
        return redirect(url_for('dashboard.dashboard'))

    with open(USER_FILE, 'r') as f:
        users = json.load(f)

    if new_custodian not in users or users[new_custodian].get("role") != "custodian":
        flash("That user is not a valid custodian", "danger")
        return redirect(url_for('dashboard.dashboard'))

    # Add to issuer's 'manages' list
    manages = users[issuer].get("manages", [])
    if new_custodian not in manages:
        manages.append(new_custodian)
        users[issuer]["manages"] = manages

        with open(USER_FILE, 'w') as f:
            json.dump(users, f, indent=4)

        flash(f"Custodian '{new_custodian}' added successfully", "success")
    else:
        flash(f"Custodian '{new_custodian}' is already associated with you", "info")

    return redirect(url_for('dashboard.dashboard'))


