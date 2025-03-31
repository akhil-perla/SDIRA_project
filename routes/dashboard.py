
from flask import Blueprint, render_template, session, redirect, url_for, flash
import json

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def dashboard():
    if 'user' not in session:
        if not session.get('_redirected'):  # Prevent multiple flash messages
            flash('You need to log in first.', 'danger')
            session['_redirected'] = True  # Set a flag so it doesn’t repeat
        return redirect(url_for('auth.login'))
    
    session.pop('_redirected', None)  # Reset the flag after login
    return render_template('dashboard.html', user=session.get('user'))

FILES_FILE = "files.json"

def load_files():
    """Load file metadata from files.json."""
    try:
        with open(FILES_FILE, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def show_issuer_dashboard():
    issuer = input("Enter your username (issuer): ").strip()
    files = load_files()

    issuer_files = {name: data for name, data in files.items() if data["issuer"] == issuer}

    if not issuer_files:
        print("You have not uploaded any files.")
        return

    print("\nYour Uploaded Files:")
    for filename, data in issuer_files.items():
        print(f"- {filename} (Custodians: {', '.join(data['custodians'])})")

if __name__ == "__main__":
    show_issuer_dashboard()

