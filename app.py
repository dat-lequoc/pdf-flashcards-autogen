from flask import Flask, request, jsonify, render_template, make_response, send_from_directory
from litellm import completion
import os
import json
from datetime import datetime
import base64
from llm_utils import generate_completion

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

    try:
        # Use llm_utils to generate completion
        content = generate_completion(prompt)
        print(prompt)
        print(content)

        if mode == 'language':
            # Parse language learning format
            lines = content.split('\n')
            word = ''
            translation = ''
            answer = ''
            for line in lines:
                if line.startswith('T:'):
                    translation = line[2:].strip()
                elif line.startswith('Q:'):
                    word = line[2:].split('<b>')[1].split('</b>')[0].strip()
                    question = line[2:].strip()
                elif line.startswith('A:'):
                    answer = line[2:].strip()
            
            flashcard = {
                'word': word,
                'question': question,
                'translation': translation,
                'answer': answer
            }
            return jsonify({'flashcard': flashcard})
            
        elif mode == 'flashcard' or 'flashcard' in prompt.lower():
            # Parse flashcard format
            flashcards = []
            current_question = ''
            current_answer = ''

            for line in content.split('\n'):
                if line.startswith('Q:'):
                    if current_question and current_answer:
                        flashcards.append({'question': current_question, 'answer': current_answer})
                    current_question = line[2:].strip()
                    current_answer = ''
                elif line.startswith('A:'):
                    current_answer = line[2:].strip()

            if current_question and current_answer:
                flashcards.append({'question': current_question, 'answer': current_answer})

            return jsonify({'flashcards': flashcards})
            
        elif mode == 'explain' or 'explain' in prompt.lower():
            # Return explanation format
            return jsonify({'explanation': content})
            
        else:
            return jsonify({'error': 'Invalid mode'}), 400
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
if __name__ == '__main__':
    # Use environment variables to determine the run mode
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug_mode, host='0.0.0.0', port=7860)
