from flask import Flask, request, jsonify, render_template, make_response, send_from_directory
from litellm import completion
import os
import json
from datetime import datetime
import base64
from llm_utils import generate_completion
import re

app = Flask(__name__)

# Use an environment variable for the upload folder, with a default to /tmp/uploads
UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', '/tmp/uploads')

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')
@app.route('/')
def index():
    recent_files = get_recent_files()
    response = make_response(render_template('index.html', recent_files=recent_files))
    return response

def get_recent_files():
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    valid_files = [f for f in files if f.lower().endswith(('.pdf', '.txt'))]
    valid_files.sort(key=lambda x: os.path.getmtime(os.path.join(app.config['UPLOAD_FOLDER'], x)), reverse=True)
    return [{'filename': file, 'date': datetime.fromtimestamp(os.path.getmtime(os.path.join(app.config['UPLOAD_FOLDER'], file))).isoformat()} for file in valid_files[:5]]

@app.route('/get_recent_files')
def get_recent_files_route():
    return jsonify(get_recent_files())

@app.route('/upload_file', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and (file.filename.lower().endswith(('.pdf', '.txt', '.epub'))):
        filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filename)
        return jsonify({'message': 'File uploaded successfully', 'filename': file.filename}), 200
    return jsonify({'error': 'Invalid file type. Please upload a PDF, TXT, or EPUB file.'}), 400

@app.route('/get_epub_content/<path:filename>')
def get_epub_content(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path) and filename.endswith('.epub'):
        with open(file_path, 'rb') as file:
            epub_content = base64.b64encode(file.read()).decode('utf-8')
        return jsonify({'epub_content': epub_content})
    return jsonify({'error': 'File not found or not an EPUB'}), 404

@app.route('/open_pdf/<path:filename>')
def open_pdf(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/generate_flashcard', methods=['POST'])
def generate_flashcard():
    data = request.json
    prompt = data['prompt']
    mode = data.get('mode', 'flashcard')
    model = data.get('model')

    try:
        # Use llm_utils to generate completion with the selected model
        content = generate_completion(prompt, model=model)
        print(prompt)
        print(content)

        if mode == 'language':
            try:
                # Extract the JSON substring from the content in case there is extra text.
                json_match = re.search(r'\{[\s\S]*\}', content)
                if json_match:
                    json_text = json_match.group(0)
                    flashcard = json.loads(json_text)
                    return jsonify({'flashcard': flashcard})
                else:
                    raise ValueError("No JSON object found in response")
            except Exception as parse_err:
                return jsonify({'error': 'JSON parsing error in language mode: ' + str(parse_err)})
        elif mode == 'flashcard':
            try:
                # Expecting a JSON array, each element having "question" and "answer"
                flashcards = json.loads(content)
                return jsonify({'flashcards': flashcards})
            except Exception as parse_err:
                return jsonify({'error': 'JSON parsing error in flashcard mode: ' + str(parse_err)})
        elif mode == 'explain':
            try:
                # Try loading JSON with an "explanation" key; fallback to plain text if not provided
                parsed = json.loads(content)
                explanation = parsed.get('explanation', content)
                return jsonify({'explanation': explanation})
            except Exception as parse_err:
                return jsonify({'explanation': content})
        else:
            return jsonify({'error': 'Invalid mode'}), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 500
if __name__ == '__main__':
    # Use environment variables to determine the run mode
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug_mode, host='0.0.0.0', port=7860)
