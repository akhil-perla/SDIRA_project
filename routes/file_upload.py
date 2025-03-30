import os
import json
import mimetypes
from datetime import datetime
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from flask import send_from_directory, abort

file_upload = Blueprint("file_upload", __name__)

UPLOAD_FOLDER = "uploads"
METADATA_FILE = "storage/files.json"
ALLOWED_EXTENSIONS = {"csv", "xlsx", "xls"}

# Ensure required directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs("storage", exist_ok=True)

def allowed_file(filename):
    """Check if the file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_mime_type(filename):
    """Get the MIME type of a file."""
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type if mime_type else "application/octet-stream"


def load_metadata():
    """Load metadata from files.json, handling corruption issues."""
    if not os.path.exists(METADATA_FILE):
        return []  # Return an empty list if file doesn't exist

    try:
        with open(METADATA_FILE, "r") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, IOError):
        return []  # Return an empty list if there's an issue


def save_metadata(metadata):
    """Save metadata safely, preventing file corruption."""
    try:
        with open(METADATA_FILE, "w") as f:
            json.dump(metadata, f, indent=4)
    except IOError as e:
        print(f"Error saving metadata: {e}")

# Function to check if a file with the same name already exists
def file_exists(filename):
    """Check if the file already exists in the upload folder."""
    return os.path.exists(os.path.join(UPLOAD_FOLDER, filename))

# Function to validate if a custodian exists (this will be based on a mock user validation)
def is_valid_custodian(username):
    """Check if the given username is a valid custodian."""
    # Here you would normally query a database or another file (e.g., users.json)
    # For simplicity, let's assume all custodians are valid if they are non-empty strings.
    users = load_users()  # Assuming we have a function to load users from a file or DB
    return username in users and users[username]["role"] == "custodian"

def load_users():
    """Load users from a mock user database (users.json)."""
    USER_FILE = "storage/users.json"
    if not os.path.exists(USER_FILE):
        return {}
    with open(USER_FILE, "r") as f:
        return json.load(f)

@file_upload.route("/upload", methods=["POST"])
def upload_file():
    """Handle file upload and add metadata to files.json."""
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        
        # Check if the file already exists
        if file_exists(filename):
            return jsonify({"error": "File with the same name already exists"}), 400
        
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)  # Save file to uploads folder

        # Prompt the issuer for custodian usernames
        custodians_input = request.form.get('custodians')
        custodians = custodians_input.split(',')

        # Validate custodians
        invalid_custodians = [custodian for custodian in custodians if not is_valid_custodian(custodian)]
        if invalid_custodians:
            return jsonify({"error": f"Invalid custodians: {', '.join(invalid_custodians)}"}), 400

        # Store metadata
        metadata = load_metadata()
        file_metadata = {
            "filename": filename,
            "size": os.path.getsize(filepath),
            "upload_time": datetime.utcnow().isoformat(),
            "mime_type": get_mime_type(filename),
            "issuer": request.form.get('issuer'),  # Assuming issuer is passed in the form
            "custodians": custodians
        }

        metadata.append(file_metadata)  # Append new file entry
        save_metadata(metadata)  # Write back to files.json

        return jsonify({"message": "File uploaded successfully", "filename": filename}), 201

    return jsonify({"error": "Invalid file type"}), 400

@file_upload.route("/download/<filename>", methods=["GET"])
def download_file(filename):
    """Allow secure downloading of uploaded files."""
    try:
        # Ensure filename is safe
        filename = secure_filename(filename)

        # Get the full file path
        filepath = os.path.join(UPLOAD_FOLDER, filename)

        # Check if file exists
        if not os.path.exists(filepath):
            return jsonify({"error": "File not found"}), 404

        # Send the file as a download attachment
        return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)

    except Exception as e:
        print(f"Download error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@file_upload.route("/issuer/files", methods=["GET"])
def get_files_for_issuer():
    """Return a list of files uploaded by the issuer along with custodians."""
    issuer = request.args.get("issuer")  # Assuming the issuer is provided in query parameters
    metadata = load_metadata()
    
    # Filter files by issuer
    user_files = [file for file in metadata if file["issuer"] == issuer]
    
    return jsonify({"files": user_files}), 200
