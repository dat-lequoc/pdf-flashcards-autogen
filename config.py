import os

class Config:
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB limit for file uploads
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
