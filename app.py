from flask import Flask
from routes.file_upload import file_upload

app = Flask(__name__)
app.register_blueprint(file_upload)

if __name__ == "__main__":
    app.run(debug=True)
