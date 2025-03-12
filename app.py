from flask import Flask, render_template
from routes.file_upload import file_upload
from routes.dashboard import dashboard_bp  # Import your dashboard blueprint

app = Flask(__name__)
app.register_blueprint(file_upload)
app.register_blueprint(dashboard_bp)  # Register your dashboard

@app.route("/")
def index():
    return render_template("upload.html")

if __name__ == "__main__":
    app.run(debug=True)
