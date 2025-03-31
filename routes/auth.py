
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
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        confirm_password = request.form['confirm_password'].strip()
        users = load_users()

        if username in users:
            flash('Username already exists. Choose a different one.', 'danger')
        elif password != confirm_password:
            flash('Passwords do not match.', 'danger')
        elif len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
        else:
            users[username] = {'password': generate_password_hash(password)}
            save_users(users)
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('auth.login'))

    return render_template('register.html')
