from flask import Flask, redirect, url_for
from routes.auth import auth_blueprint  
from routes.dashboard import dashboard_bp
from routes.file_upload import file_upload
from routes.custodian import custodian_bp

import os

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "your_secret_key")

# Register Blueprints
app.register_blueprint(auth_blueprint, url_prefix="/auth")  # ✅ using auth_blueprint here
app.register_blueprint(dashboard_bp, url_prefix="/dashboard")
app.register_blueprint(file_upload)
app.register_blueprint(custodian_bp, url_prefix='/custodian')

for rule in app.url_map.iter_rules():
    print(f"{rule.endpoint} --> {rule.rule}")


@app.route("/")
def index():
    return redirect(url_for("auth.login"))  # 'auth' is the name of the Blueprint, not the variable

if __name__ == "__main__":
    app.run(debug=True)
