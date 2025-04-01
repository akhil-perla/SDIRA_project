from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash, generate_password_hash
import json
import os

USER_FILE = "storage/users.json"

def load_users():
    if not os.path.exists(USER_FILE):
        return {}
    with open(USER_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USER_FILE, "w") as f:
        json.dump(users, f, indent=4)

auth_blueprint = Blueprint('auth', __name__)

@auth_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        users = load_users()

        if username in users and check_password_hash(users[username]["password"], password):
            user_data = users[username]
            session['user'] = username
            session['role'] = user_data.get("role")  # Store role in session
            flash("Login successful!", "success")

            # Redirect based on role
            if user_data.get("role") == "custodian":
                return redirect(url_for("custodian.custodian_dashboard"))
            else:  # issuer or default
                return redirect(url_for("dashboard.dashboard"))
        else:
            flash("Invalid credentials", "danger")

    return render_template('login.html')

@auth_blueprint.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        confirm_password = request.form['confirm_password'].strip()
        role = request.form['role']
        manages = request.form.get('manages', "").strip()
        
        users = load_users()

        if username in users:
            flash('Username already exists. Choose a different one.', 'danger')
        elif password != confirm_password:
            flash('Passwords do not match.', 'danger')
        elif len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
        else:
            user_data = {
                "password": generate_password_hash(password),
                "role": role
            }
            if role == "custodian" and manages:
                user_data["manages"] = [m.strip() for m in manages.split(",") if m.strip()]

            users[username] = user_data
            save_users(users)

            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('auth.login'))

    return render_template('register.html')


# Define the logout route
@auth_blueprint.route('/logout')
def logout():
    # Remove user from session to log out
    session.pop('user', None)
    return redirect(url_for('auth.login'))  # Redirect to login page after logout
