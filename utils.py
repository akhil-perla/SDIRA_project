import json
import threading
import os
from datetime import datetime

lock = threading.Lock()  # Prevent concurrent write issues

# Define storage directory
STORAGE_DIR = "storage"

# Ensure storage directory exists
os.makedirs(STORAGE_DIR, exist_ok=True)

def get_file_path(filename):
    """Returns the full path of the JSON file inside the storage directory."""
    # Add basic filename validation
    if not filename or not isinstance(filename, str):
        raise ValueError("Invalid filename")
    return os.path.join(STORAGE_DIR, filename)

def load_json(filename):
    filepath = get_file_path(filename)
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            return json.load(f)
    return {"files": []} if filename == "files.json" else {"users": []}

def save_json(filename, data):
    if not os.path.exists(STORAGE_DIR):
        os.makedirs(STORAGE_DIR)
    filepath = get_file_path(filename)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4)

def authenticate_user(username, password):
    users = load_json('users.json')
    for user in users['users']:
        if user['username'] == username and user['password'] == password:
            return user['token']
    return None

def verify_token(token):
    users = load_json('users.json')
    return any(user['token'] == token for user in users['users'])

def add_file(filename, file_type, size):
    files = load_json('files.json')
    files['files'].append({
        'filename': filename,
        'type': file_type,
        'size': size,
        'uploaded_at': datetime.now().isoformat()
    })
    save_json('files.json', files)

def get_files():
    return load_json('files.json')['files']

def save_json_threadsafe(filename, data):
    """Write data to a JSON file with thread safety."""
    filepath = get_file_path(filename)

    # Ensure the directory exists before writing
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    with lock:  # Ensure only one thread writes at a time
        try:
            # Create temporary file first
            temp_filepath = filepath + '.tmp'
            with open(temp_filepath, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=4)
            # Atomic rename for safer file writing
            os.replace(temp_filepath, filepath)
        except Exception as e:
            print(f"Error writing to {filepath}: {e}")
            # Clean up temp file if it exists
            if os.path.exists(temp_filepath):
                os.remove(temp_filepath)
            raise  # Re-raise the exception after cleanup
