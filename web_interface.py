#!/usr/bin/env python3
"""
Flask Web Interface for Playlist Importer
Allows users to upload files, configure folder mappings, and manage file types
"""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import json
import os
import shutil
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'

# Configuration file path
CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config.json')

def load_config():
    """Load configuration from config.json"""
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def save_config(config):
    """Save configuration to config.json"""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

@app.route('/')
def index():
    """Main dashboard"""
    config = load_config()
    return render_template('index.html', config=config)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    """File upload page"""
    if request.method == 'POST':
        config = load_config()
        import_folder = config['directories']['import_folder']

        # Check if files were uploaded
        if 'files[]' not in request.files:
            flash('No files selected', 'error')
            return redirect(request.url)

        files = request.files.getlist('files[]')
        uploaded_count = 0

        for file in files:
            if file and file.filename:
                filename = secure_filename(file.filename)
                file_ext = os.path.splitext(filename)[1][1:].upper()

                # Check if file type is allowed
                if file_ext in [ft.upper() for ft in config['allowed_file_types']]:
                    file_path = os.path.join(import_folder, filename)
                    file.save(file_path)
                    uploaded_count += 1
                else:
                    flash(f'File type .{file_ext} not allowed for {filename}', 'warning')

        if uploaded_count > 0:
            flash(f'Successfully uploaded {uploaded_count} file(s)', 'success')

        return redirect(url_for('upload'))

    config = load_config()
    return render_template('upload.html', config=config)

@app.route('/configure')
def configure():
    """Configuration page"""
    config = load_config()
    return render_template('configure.html', config=config)

@app.route('/api/folder_mappings', methods=['GET', 'POST', 'DELETE'])
def manage_folder_mappings():
    """API endpoint for managing folder mappings"""
    config = load_config()

    if request.method == 'GET':
        return jsonify(config['folder_mappings'])

    elif request.method == 'POST':
        data = request.json
        prefix = data.get('prefix', '').strip()
        folder = data.get('folder', '').strip()

        if not prefix or not folder:
            return jsonify({'error': 'Prefix and folder are required'}), 400

        config['folder_mappings'][prefix] = folder
        save_config(config)
        return jsonify({'success': True, 'message': 'Mapping added successfully'})

    elif request.method == 'DELETE':
        prefix = request.json.get('prefix')

        if prefix in config['folder_mappings']:
            del config['folder_mappings'][prefix]
            save_config(config)
            return jsonify({'success': True, 'message': 'Mapping deleted successfully'})

        return jsonify({'error': 'Mapping not found'}), 404

@app.route('/api/file_types', methods=['GET', 'POST'])
def manage_file_types():
    """API endpoint for managing allowed file types"""
    config = load_config()

    if request.method == 'GET':
        return jsonify(config['allowed_file_types'])

    elif request.method == 'POST':
        data = request.json
        file_types = data.get('file_types', [])

        # Validate file types (should be uppercase, 2-4 characters)
        valid_types = []
        for ft in file_types:
            ft = ft.strip().upper()
            if ft and len(ft) >= 2 and len(ft) <= 4 and ft.isalnum():
                valid_types.append(ft)

        if valid_types:
            config['allowed_file_types'] = valid_types
            save_config(config)
            return jsonify({'success': True, 'message': 'File types updated successfully'})

        return jsonify({'error': 'No valid file types provided'}), 400

@app.route('/api/directories', methods=['GET', 'POST'])
def manage_directories():
    """API endpoint for managing directory paths"""
    config = load_config()

    if request.method == 'GET':
        return jsonify(config['directories'])

    elif request.method == 'POST':
        data = request.json
        dir_type = data.get('type')
        path = data.get('path', '').strip()

        if dir_type not in config['directories']:
            return jsonify({'error': 'Invalid directory type'}), 400

        if not path:
            return jsonify({'error': 'Path is required'}), 400

        config['directories'][dir_type] = path
        save_config(config)
        return jsonify({'success': True, 'message': 'Directory updated successfully'})

@app.route('/logs')
def view_logs():
    """View recent log files"""
    config = load_config()
    log_folder = config['directories']['log_folder']

    logs = []
    if os.path.exists(log_folder):
        log_files = sorted(
            [f for f in os.listdir(log_folder) if f.startswith('PlaylistImporter-')],
            reverse=True
        )

        for log_file in log_files[:10]:  # Show last 10 log files
            log_path = os.path.join(log_folder, log_file)
            logs.append({
                'filename': log_file,
                'date': log_file.replace('PlaylistImporter-', '').replace('.txt', ''),
                'size': os.path.getsize(log_path)
            })

    return render_template('logs.html', logs=logs)

@app.route('/logs/<filename>')
def view_log_file(filename):
    """View a specific log file"""
    config = load_config()
    log_folder = config['directories']['log_folder']
    log_path = os.path.join(log_folder, secure_filename(filename))

    if not os.path.exists(log_path) or not filename.startswith('PlaylistImporter-'):
        flash('Log file not found', 'error')
        return redirect(url_for('view_logs'))

    with open(log_path, 'r') as f:
        log_content = f.read()

    return render_template('log_detail.html', filename=filename, content=log_content)

if __name__ == '__main__':
    # Run on all interfaces so it can be accessed from other machines
    app.run(host='0.0.0.0', port=5000, debug=True)
