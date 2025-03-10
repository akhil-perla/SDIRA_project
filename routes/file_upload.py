import os
import json
from flask import Blueprint, request, render_template, send_from_directory, jsonify

# Configure blueprint
file_upload = Blueprint("file_upload", __name__)

# Allowed file extensions
ALLOWED_EXTENSIONS = {"csv", "xls", "xlsx"}
UPLOAD_FOLDER = "uploads"
METADATA_FILE = "storage/files.json"
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs("storage", exist_ok=True)

# Function to check file extension
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# Load existing metadata
def load_metadata():
    if not os.path.exists(METADATA_FILE):
        return []
    with open(METADATA_FILE, "r") as f:
        return json.load(f)

# Save metadata
def save_metadata(metadata):
    with open(METADATA_FILE, "w") as f:
        json.dump(metadata, f, indent=4)

# Route for file upload
@file_upload.route("/upload", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        if "file" not in request.files:
            return jsonify({"error": "No file part"}), 400

        file = request.files["file"]

        if file.filename == "":
            return jsonify({"error": "No selected file"}), 400

        if not allowed_file(file.filename):
            return jsonify({"error": "Invalid file type"}), 400

        if request.content_length > MAX_FILE_SIZE:
            return jsonify({"error": "File is too large"}), 400

        # Save file
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)

        # Update metadata
        metadata = load_metadata()
        metadata.append({"filename": file.filename, "size": os.path.getsize(filepath)})
        save_metadata(metadata)

        return jsonify({"message": "File uploaded successfully", "filename": file.filename}), 200

    return render_template("upload.html")

# Route for secure file download
@file_upload.route("/download/<filename>", methods=["GET"])
def download_file(filename):
    try:
        return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)
    except FileNotFoundError:
        return jsonify({"error": "File not found"}), 404
