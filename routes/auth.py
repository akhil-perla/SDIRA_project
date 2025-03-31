
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash, generate_password_hash
import json
import os

# Load users from users.json
USER_FILE = "storage/users.json"

def load_users():
    if not os.path.exists(USER_FILE):
        return {}
    with open(USER_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USER_FILE, "w") as f:
        json.dump(users, f, indent=4)

auth = Blueprint('auth', __name__)

# LOGIN ROUTE
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if 'user' in session:
        flash('You are already logged in.', 'info')
        return redirect(url_for('dashboard.dashboard'))  # Redirect if already logged in
    
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        users = load_users()

        if username in users and check_password_hash(users[username]['password'], password):
            session['user'] = username  # Store session
            session.modified = True  # Ensure session is saved
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard.dashboard'))
        else:
            flash('Invalid username or password', 'danger')

    return render_template('login.html')

# LOGOUT ROUTE
@auth.route('/logout')
def logout():
    if 'user' in session:
        session.clear()  # Completely clear session data
        flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

# REGISTER ROUTE
@auth.route('/register', methods=['GET', 'POST'])
def register_user():
    users = load_users()

    username = input("Enter username: ").strip()
    if username in users:
        print("Error: Username already exists!")
        return
    
    password = getpass.getpass("Enter password: ").strip()  # Secure input
    role = input("Enter role (admin, custodian, issuer, user): ").strip().lower()
    
    if role not in ["admin", "custodian", "issuer", "user"]:
        print("Error: Invalid role. Must be admin, custodian, issuer, or user.")
        return
    
    manages = []
    if role in ["custodian", "issuer"]:
        manages = input(f"Enter associated {'issuers' if role == 'custodian' else 'custodians'} (comma-separated): ").strip().split(",")

    users[username] = {
        "password": password,  # Keeping existing encryption format
        "role": role,
        "manages": [m.strip() for m in manages if m.strip()]
    }

    save_users(users)
    print(f"User '{username}' registered successfully!")

if __name__ == "__main__":
    register_user()
