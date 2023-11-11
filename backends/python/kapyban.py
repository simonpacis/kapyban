import yaml
from flask import Flask, request, send_from_directory, jsonify, abort, render_template_string
import os
import json

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'boards'
ALLOWED_EXTENSIONS = {'json'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Load passwords from YAML
try:
    with open('passwords.yaml', 'r') as file:
        password_data = yaml.safe_load(file)
        FALLBACK_PASSWORD = password_data['fallback_password']
        FILE_PASSWORDS = password_data['file_passwords']
except FileNotFoundError:
    raise Exception("passwords.yaml file not found. Application cannot start without it.")
except yaml.YAMLError as e:
    raise Exception(f"Error reading passwords.yaml: {e}")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_password(filename, password):
    file_password = FILE_PASSWORDS.get(filename, FALLBACK_PASSWORD)
    return password == file_password

@app.route('/upload/<filename>', methods=['POST'])
def upload_file(filename):
    if 'file' not in request.files or 'password' not in request.form:
        return jsonify(error="File or password not provided"), 400

    file = request.files['file']
    password = request.form['password']

    if file.filename == '' or not allowed_file(file.filename):
        return jsonify(error="Invalid file"), 400

    if not validate_password(filename, password):
        return jsonify(error="Invalid password"), 403

    file.save(os.path.join(UPLOAD_FOLDER, filename + '.json'))
    return jsonify(success=True)

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename + '.json', as_attachment=True)

@app.route('/<filename>', methods=['GET'])
def view_file(filename):
    try:
        with open(os.path.join(UPLOAD_FOLDER, filename + '.json'), 'r') as file:
            content = json.load(file)
            visual_body = content.get('board_visual', '')
            html_template = f'''
                <!doctype html>
                <html>
                <head>
                    <title>Kapyban Kanban Board</title>
                </head>
                <body>
                    {visual_body}
                </body>
                </html>
            '''
            return render_template_string(html_template)
    except FileNotFoundError:
        abort(404)

@app.errorhandler(404)
def not_found(error):
    return jsonify(error="File not found"), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify(error="Server error"), 500

if __name__ == '__main__':
    app.run(debug=False, port=80)

