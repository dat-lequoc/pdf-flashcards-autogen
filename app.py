from flask import Flask, request, jsonify, render_template, make_response, send_from_directory
import anthropic
import os
import json
from datetime import datetime

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

@app.route('/')
def index():
    recent_pdfs = get_recent_pdfs()
    return render_template('index.html', recent_pdfs=recent_pdfs)

def get_recent_pdfs():
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    pdf_files = [f for f in files if f.endswith('.pdf')]
    pdf_files.sort(key=lambda x: os.path.getmtime(os.path.join(app.config['UPLOAD_FOLDER'], x)), reverse=True)
    return [{'filename': pdf, 'date': datetime.fromtimestamp(os.path.getmtime(os.path.join(app.config['UPLOAD_FOLDER'], pdf))).isoformat()} for pdf in pdf_files[:5]]

@app.route('/upload_pdf', methods=['POST'])
def upload_pdf():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and file.filename.endswith('.pdf'):
        filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filename)
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

    client = anthropic.Anthropic(api_key=api_key)

    try:
        model = data.get('model', 'claude-3-haiku-20240307')
        message = client.messages.create(
            model=model,
            max_tokens=1024,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        content = message.content[0].text
        print(content)
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

        response = make_response(jsonify({'flashcards': flashcards}))

        # Set cookie with the API key
        response.set_cookie('last_working_api_key', api_key, secure=True, httponly=True, samesite='Strict')

        return response
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
