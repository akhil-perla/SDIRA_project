from flask import Flask, render_template, redirect, url_for
from routes.file_upload import file_upload
from routes.dashboard import dashboard_bp  # Import dashboard blueprint
from routes.auth import auth_blueprint # Assuming 'auth' is in a module called auth

# Initialize Flask App
app = Flask(__name__)
app.secret_key = "your_secret_key"  # Set a secure key for sessions

# Register Blueprints
app.register_blueprint(file_upload)
app.register_blueprint(auth_blueprint, url_prefix='/auth')
app.register_blueprint(dashboard_bp, url_prefix='/dashboard')

@app.route("/")
def index():
    return redirect(url_for("auth.login"))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Retrieve the user from users.json
        with open('users.json') as f:
            users = json.load(f)

        user = users.get(username)
        if user and check_password_hash(user['password'], password):
            # Store the username in the session
            session['user'] = username
            flash('Login successful!', 'success')
            return redirect('/dashboard')  # Redirect to dashboard after successful login
        else:
            flash('Invalid credentials, please try again.', 'error')

    return render_template('login.html')  # If GET method or invalid login, render login form

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:  # Check if 'user' is in session
        flash('You must be logged in to view the dashboard.', 'error')  # Show a flash message
        return redirect('/login')  # Redirect to login if not logged in

    username = session['user']  # Retrieve the logged-in user's username from session
    return render_template('dashboard.html', username=username)  # Pass the username to the template


if __name__ == "__main__":
    app.run(debug=True)