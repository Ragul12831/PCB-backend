from flask import Flask, render_template, request, jsonify, send_file, abort
from flask_cors import CORS
import os
import json
from pathlib import Path

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# Configuration
UPLOAD_FOLDER = 'pcb_files'
ALLOWED_EXTENSIONS = {'kicad_pcb', 'pcb'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_valid_pcb_path(file_path):
    """Check if the provided path is valid and points to a PCB file"""
    try:
        path = Path(file_path)
        return path.exists() and path.is_file() and path.suffix.lower() in ['.kicad_pcb', '.pcb']
    except:
        return False

@app.route('/api/load-pcb', methods=['POST'])
def load_pcb():
    """API endpoint to load PCB from system path"""
    try:
        data = request.get_json()
        file_path = data.get('file_path', '')
        
        if not file_path:
            return jsonify({'error': 'No file path provided'}), 400
        
        # Validate the file path
        if not is_valid_pcb_path(file_path):
            return jsonify({'error': 'Invalid PCB file path or file does not exist'}), 400
        
        # Copy file to our upload folder with a unique name
        source_path = Path(file_path)
        filename = f"current_pcb{source_path.suffix}"
        destination = Path(app.config['UPLOAD_FOLDER']) / filename
        
        # Create upload folder if it doesn't exist
        destination.parent.mkdir(exist_ok=True)
        
        # Copy the file
        import shutil
        shutil.copy2(source_path, destination)
        
        return jsonify({
            'success': True,
            'filename': filename,
            'original_path': file_path,
            'url': f'/pcb/{filename}'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/pcb/<filename>')
def serve_pcb(filename):
    """Serve PCB files"""
    try:
        file_path = Path(app.config['UPLOAD_FOLDER']) / filename
        if not file_path.exists():
            abort(404)
        return send_file(file_path, as_attachment=False)
    except Exception as e:
        abort(404)

@app.route('/api/validate-path', methods=['POST'])
def validate_path():
    """Validate if a given path is a valid PCB file"""
    try:
        data = request.get_json()
        file_path = data.get('file_path', '')
        
        is_valid = is_valid_pcb_path(file_path)
        
        response = {
            'valid': is_valid,
            'path': file_path
        }
        
        if is_valid:
            path = Path(file_path)
            response['file_info'] = {
                'name': path.name,
                'size': path.stat().st_size,
                'extension': path.suffix
            }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Create upload folder if it doesn't exist
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000)