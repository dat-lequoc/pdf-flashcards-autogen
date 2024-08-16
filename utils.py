import os
from datetime import datetime
from flask import current_app

def get_recent_pdfs():
    if not os.path.exists(current_app.config['UPLOAD_FOLDER']):
        os.makedirs(current_app.config['UPLOAD_FOLDER'])
    files = os.listdir(current_app.config['UPLOAD_FOLDER'])
    pdf_files = [f for f in files if f.endswith('.pdf')]
    pdf_files.sort(key=lambda x: os.path.getmtime(os.path.join(current_app.config['UPLOAD_FOLDER'], x)), reverse=True)
    return [{'filename': pdf, 'date': datetime.fromtimestamp(os.path.getmtime(os.path.join(current_app.config['UPLOAD_FOLDER'], pdf))).isoformat()} for pdf in pdf_files[:5]]

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
import os
from datetime import datetime
from flask import current_app

def get_recent_pdfs():
    if not os.path.exists(current_app.config['UPLOAD_FOLDER']):
        os.makedirs(current_app.config['UPLOAD_FOLDER'])
    files = os.listdir(current_app.config['UPLOAD_FOLDER'])
    pdf_files = [f for f in files if f.endswith('.pdf')]
    pdf_files.sort(key=lambda x: os.path.getmtime(os.path.join(current_app.config['UPLOAD_FOLDER'], x)), reverse=True)
    return [{'filename': pdf, 'date': datetime.fromtimestamp(os.path.getmtime(os.path.join(current_app.config['UPLOAD_FOLDER'], pdf))).isoformat()} for pdf in pdf_files[:5]]
