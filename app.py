from flask import Flask, request, jsonify, render_template, make_response, send_from_directory
import anthropic
import os
import json
from datetime import datetime
import base64

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

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
    return [{'filename': file, 'date': datetime.fromtimestamp(os.path.getmtime(os.path.join(app.config['UPLOAD_FOLDER'], file))).isoformat()} for file in valid_files[:10]]

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
    api_key = request.headers.get('X-API-Key')
    mode = data.get('mode', 'flashcard')

    client = anthropic.Anthropic(api_key=api_key)

    try:
        model = data.get('model', "claude-3-5-sonnet-20240620")
        message = client.messages.create(
            model=model,
            max_tokens=1024,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        content = message.content[0].text
        print(prompt)
        print('-'*10)
        print(content)

        if "Translate the text below" in prompt:
            response = make_response(jsonify({'translation': content}))

        elif mode == 'language':
            # For Language mode, parse the content and return in the custom format
            import re

            translation = re.search(r'<T>(.*?)</T>', content, re.DOTALL)
            question = re.search(r'<Q>(.*?)</Q>', content, re.DOTALL)
            answer = re.search(r'<A>(.*?)</A>', content, re.DOTALL)
            
            if question:
                word = re.search(r'<b>(.*?)</b>', question.group(1))
                word = word.group(1) if word else ''
            else:
                word = ''

            flashcard = {
                'word': word,
                'question': question.group(1).strip() if question else '',
                'translation': translation.group(1).strip() if translation else '',
                'answer': answer.group(1).strip() if answer else ''
            }
            response = make_response(jsonify({'flashcard': flashcard}))
        elif mode == 'flashcard' or 'flashcard' in prompt.lower():
            import re

            flashcards = []
            qa_pairs = re.findall(r'<Q>(.*?)</Q>\s*<A>(.*?)</A>', content, re.DOTALL)

            for question, answer in qa_pairs:
                flashcards.append({
                    'question': question.strip(),
                    'answer': answer.strip()
                })

            response = make_response(jsonify({'flashcards': flashcards}))
        elif mode == 'explain' or 'explain' in prompt.lower():
            # For Explain mode, return the entire content as the explanation
            response = make_response(jsonify({'explanation': content}))
        else:
            response = make_response(jsonify({'error': 'Invalid mode'}))

        # Set cookie with the API key
        response.set_cookie('last_working_api_key', api_key, secure=True, httponly=True, samesite='Strict')

        return response
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
