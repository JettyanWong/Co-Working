import os
from dotenv import load_dotenv

# Load .env from the backend directory
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    ENV = os.getenv('FLASK_ENV', 'production')

    # Determine database URI
    _env = os.getenv('FLASK_ENV', 'production')
    _db_url = os.getenv('DATABASE_URL', '').strip()

    if _db_url:
        SQLALCHEMY_DATABASE_URI = _db_url
    elif _env == 'development':
        SQLALCHEMY_DATABASE_URI = 'sqlite:///coworking.db'
    else:
        SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:password@localhost:3306/coworking'

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    _default_upload = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'uploads')
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', _default_upload)
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 100 * 1024 * 1024))
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'png', 'jpg', 'jpeg', 'gif'}

    # Security settings
    SESSION_COOKIE_SECURE = ENV == 'production'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # CORS settings - restrict in production
    if ENV == 'production':
        CORS_ORIGINS = os.getenv('CORS_ORIGINS', '').split(',') if os.getenv('CORS_ORIGINS') else []
    else:
        CORS_ORIGINS = '*'
