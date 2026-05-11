from flask import Flask, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_socketio import SocketIO
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
import os

db = SQLAlchemy()
login_manager = LoginManager()
socketio = SocketIO()
limiter = Limiter(key_func=get_remote_address)

# Get the directory paths
# __file__ is /Volumes/Jett/projects/Co-working/backend/app/__init__.py
# Structure: Co-working/backend/app/__init__.py -> Co-working/frontend/
APP_DIR = os.path.dirname(os.path.abspath(__file__))  # .../backend/app
BACKEND_DIR = os.path.dirname(APP_DIR)  # .../backend
PROJECT_DIR = os.path.dirname(BACKEND_DIR)  # .../Co-working
FRONTEND_DIR = os.path.join(PROJECT_DIR, 'frontend')


def create_app():
    app = Flask(__name__, static_folder=None)  # Disable Flask's default static handler

    from app.config import Config
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    socketio.init_app(app, cors_allowed_origins="*", async_mode='eventlet')
    limiter.init_app(app)

    # Configure CORS based on environment
    cors_origins = getattr(Config, 'CORS_ORIGINS', '*')
    CORS(app, origins=cors_origins)

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Health check endpoint
    @app.route('/api/health')
    def health_check():
        return jsonify({'status': 'healthy', 'service': 'coworking'})

    # Serve frontend files
    @app.route('/')
    def index():
        return send_from_directory(FRONTEND_DIR, 'login.html')

    @app.route('/login.html')
    def login():
        return send_from_directory(FRONTEND_DIR, 'login.html')

    @app.route('/static/<path:filename>')
    def static_files(filename):
        return send_from_directory(os.path.join(FRONTEND_DIR, 'static'), filename)

    from app.routes import auth, users, projects, tasks, documents, files
    app.register_blueprint(auth.bp)
    app.register_blueprint(users.bp)
    app.register_blueprint(projects.bp)
    app.register_blueprint(tasks.bp)
    app.register_blueprint(documents.bp)
    app.register_blueprint(files.bp)

    # Import collab service to register socket handlers
    from app.services import collab

    with app.app_context():
        db.create_all()
        # Migration: add status column and activate existing users
        try:
            db.session.execute(db.text("ALTER TABLE users ADD COLUMN status VARCHAR(10) DEFAULT 'pending'"))
            db.session.commit()
            # Column was just added — existing users predate the approval system, activate them
            db.session.execute(db.text("UPDATE users SET status = 'active'"))
            db.session.commit()
        except Exception:
            db.session.rollback()

    return app
