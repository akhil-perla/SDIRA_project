from werkzeug.security import check_password_hash
from flask import flash
from routes.file_upload import file_upload
from routes.dashboard import dashboard_bp  # Import dashboard blueprint
from routes.auth import auth_blueprint  # Assuming 'auth' is in a module called auth
import os
import json
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
from werkzeug.utils import secure_filename
from datetime import datetime

# Initialize Flask App
app = Flask(__name__)
app.secret_key = "your_secret_key"  # Set a secure key for sessions

# Register Blueprints
app.register_blueprint(file_upload)
app.register_blueprint(auth_blueprint, url_prefix='/auth')
app.register_blueprint(dashboard_bp, url_prefix='/dashboard')

# Configure the file upload settings
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'csv', 'xlsx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Make sure the directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Utility function to check allowed file types
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Route for the dashboard
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user' not in session:
        return redirect(url_for('auth.login'))  # Redirect to login if not authenticated

    # Get files of the current user
    user_files = get_user_files(session['user'])

    if request.method == 'POST':
        # Handle file upload
        if 'file' not in request.files:
            flash('No file part', 'error')
            return redirect(request.url)
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # Get file metadata
            file_size = os.path.getsize(filepath)  # Get file size
            file_type = filename.rsplit('.', 1)[1].lower()  # Get file extension
            upload_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Get current timestamp

            # Save file metadata
            save_file_info(session['user'], filename, file_size, file_type, upload_time)
            flash('File uploaded successfully!', 'success')
            return redirect(url_for('dashboard'))

    return render_template('dashboard.html', user=session['user'], files=user_files)

# Function to get the list of files for a specific user
def get_user_files(user):
    try:
        # Read the user-specific files JSON file
        with open(f'{user}_files.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []  # Return empty list if no files exist for the user

# Function to save file info (this can be a database call)
def save_file_info(user, filename, file_size, file_type, upload_time):
    user_files = get_user_files(user)
    user_files.append({
        "filename": filename,
        "size": file_size,
        "type": file_type,
        "upload_time": upload_time
    })
    with open(f'{user}_files.json', 'w') as f:
        json.dump(user_files, f, indent=4)

# Route for downloading files
@app.route('/uploads/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

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

if __name__ == "__main__":
    app.run(debug=True)
