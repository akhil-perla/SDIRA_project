from flask import Flask, redirect, url_for, request, flash, render_template, session
from routes.auth import auth_blueprint  
from routes.dashboard import dashboard_bp
from routes.file_upload import file_upload
from routes.custodian import custodian_bp
from blueprints.uploads import uploads_bp

import os
import pandas as pd
from werkzeug.utils import secure_filename
import json
from flask_login import LoginManager, login_required, current_user

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'  # Replace with your actual secret key
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SESSION_TYPE'] = 'filesystem'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User loader function
@login_manager.user_loader
def load_user(user_id):
    # Implement your user loading logic here
    from models import User  # Import your User model
    return User.get(user_id)

# Register Blueprints
app.register_blueprint(auth_blueprint, url_prefix="/auth")  # ✅ using auth_blueprint here
app.register_blueprint(dashboard_bp, url_prefix="/dashboard")
app.register_blueprint(file_upload)
app.register_blueprint(custodian_bp, url_prefix='/custodian')
app.register_blueprint(uploads_bp)

for rule in app.url_map.iter_rules():
    print(f"{rule.endpoint} --> {rule.rule}")


@app.route("/")
def index():
    return redirect(url_for("auth.login"))  # 'auth' is the name of the Blueprint, not the variable

ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload_issuers', methods=['GET', 'POST'])
@login_required
def upload_issuers():
    # Get user data from users.json
    with open('storage/users.json', 'r') as f:
        users_data = json.load(f)
    
    # Check if user is a custodian
    if users_data.get(current_user.id, {}).get('role') != 'custodian':
        flash('Only custodians can upload issuer information', 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
        
        file = request.files['file']
        
        # If user does not select file, browser also submits an empty part without filename
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # Process the file
            try:
                process_issuer_file(file_path, current_user.id)
                flash('Issuer information uploaded successfully', 'success')
            except Exception as e:
                flash(f'Error processing file: {str(e)}', 'danger')
            
            # Clean up the file
            os.remove(file_path)
            
            return redirect(url_for('custodian_dashboard'))
    
    return render_template('upload_issuers.html')

@app.route('/upload_securities', methods=['GET', 'POST'])
@login_required
def upload_securities():
    # Get user data from users.json
    with open('storage/users.json', 'r') as f:
        users_data = json.load(f)
    
    # Check if user is a custodian
    if users_data.get(current_user.id, {}).get('role') != 'custodian':
        flash('Only custodians can upload securities information', 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
        
        file = request.files['file']
        
        # If user does not select file, browser also submits an empty part without filename
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # Process the file
            try:
                # You'll need to implement this function
                process_securities_file(file_path, current_user.id)
                flash('Securities information uploaded successfully', 'success')
            except Exception as e:
                flash(f'Error processing file: {str(e)}', 'danger')
            
            # Clean up the file
            os.remove(file_path)
            
            return redirect(url_for('custodian_dashboard'))
    
    return render_template('upload_securities.html')

@app.route('/test')
def test():
    return "Application is working!"

if __name__ == "__main__":
    app.run(debug=True)
