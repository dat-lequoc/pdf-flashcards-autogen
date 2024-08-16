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
