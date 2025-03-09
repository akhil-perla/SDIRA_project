from flask import Flask, request, jsonify
from utils import add_file, get_files

app = Flask(__name__)

@app.route('/')
def home():
    return """
    <h1>File Management API</h1>
    <p>Available endpoints:</p>
    <ul>
        <li>POST /api/upload - Upload file information</li>
        <li>GET /api/files - List all files</li>
    </ul>
    """

@app.route('/api/upload', methods=['POST'])
def upload():
    data = request.json
    add_file(data['filename'], data['type'], data['size'])
    return jsonify({"message": "File added successfully"})

@app.route('/api/files', methods=['GET'])
def list_files():
    return jsonify({"files": get_files()})

if __name__ == '__main__':
    app.run(debug=True)
