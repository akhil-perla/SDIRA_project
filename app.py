from flask import Flask, render_template
from routes.file_upload import file_upload
from routes.auth import *
from routes.dashboard import dashboard_bp  # Import dashboard blueprint


# Initialize Flask App
app = Flask(__name__)
app.secret_key = "your_secret_key"  # Set a secure key for sessions

# Register Blueprints
app.register_blueprint(file_upload)
app.register_blueprint(auth, url_prefix='/auth')
app.register_blueprint(dashboard_bp, url_prefix='/dashboard')

@app.route("/")
def index():
    return redirect(url_for("auth.login"))

if __name__ == "__main__":
    app.run(debug=True)