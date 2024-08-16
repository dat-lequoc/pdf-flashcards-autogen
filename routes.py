from flask import request, jsonify, render_template, make_response, send_from_directory
from werkzeug.utils import secure_filename
import anthropic
import os
import json
from datetime import datetime
from app import app
from utils import get_recent_pdfs

@app.route('/')
def index():
    recent_pdfs = get_recent_pdfs()
    return render_template('index.html', recent_pdfs=recent_pdfs)

@app.route('/upload_pdf', methods=['POST'])
def upload_pdf():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and file.filename.endswith('.pdf'):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return jsonify({'message': 'File uploaded successfully'}), 200
    return jsonify({'error': 'Invalid file type'}), 400

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
        print(content)

        if mode == 'language':
            flashcard = parse_language_content(content)
            response = make_response(jsonify({'flashcard': flashcard}))
        elif mode == 'flashcard' or 'flashcard' in prompt.lower():
            flashcards = parse_flashcard_content(content)
            response = make_response(jsonify({'flashcards': flashcards}))
        elif mode == 'explain' or 'explain' in prompt.lower():
            response = make_response(jsonify({'explanation': content}))
        else:
            response = make_response(jsonify({'error': 'Invalid mode'}))

        response.set_cookie('last_working_api_key', api_key, secure=True, httponly=True, samesite='Strict')

        return response
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def parse_language_content(content):
    lines = content.split('\n')
    word = ''
    translation = ''
    answer = ''
    for line in lines:
        if line.startswith('T:'):
            translation = line[2:].strip()
        elif line.startswith('Q:'):
            word = line[2:].split('<b>')[1].split('</b>')[0].strip()
        elif line.startswith('A:'):
            answer = line[2:].strip()
    
    return {
        'word': word,
        'question': lines[1][2:].strip(),
        'translation': translation,
        'answer': answer
    }

def parse_flashcard_content(content):
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

    return flashcards
