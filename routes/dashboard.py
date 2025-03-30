from flask import Blueprint, render_template, session, redirect, url_for, flash, request
import requests  # To make HTTP requests to the /issuer/files endpoint

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def dashboard():
    if 'user' not in session:
        if not session.get('_redirected'):  # Prevent multiple flash messages
            flash('You need to log in first.', 'danger')
            session['_redirected'] = True  # Set a flag so it doesn’t repeat
        return redirect(url_for('auth.login'))
    
    session.pop('_redirected', None)  # Reset the flag after login

    # Make a request to the /issuer/files endpoint to get the files for the logged-in user
    issuer = session.get('user')  # Assuming the user's username is stored in the session

    # Corrected URL to include the scheme and domain
    url = f'http://127.0.0.1:5000/issuer/files?issuer={issuer}'

    # Make the HTTP GET request
    response = requests.get(url)

    # Check if the response is valid and contains the expected data
    if response.status_code == 200:
        files_data = response.json().get('files', [])
        if not isinstance(files_data, list):
            files_data = []  # Ensure it's always a list
    else:
        flash('Failed to load your uploaded files.', 'danger')
        files_data = []

    # Ensure the user is not None and is a valid string
    user = session.get('user')
    if not user:
        flash('Invalid user session.', 'danger')
        return redirect(url_for('auth.login'))

    # Filter files for the logged-in issuer
    user_files = [file for file in files_data if file.get('issuer') == user]

    return render_template('dashboard.html', user=user, files=user_files)
