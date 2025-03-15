
from flask import Blueprint, render_template, session, redirect, url_for, flash

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



