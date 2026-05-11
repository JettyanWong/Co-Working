import os
from app import create_app, socketio

app = create_app()

if __name__ == '__main__':
    debug = os.getenv('FLASK_ENV', 'production') == 'development'
    socketio.run(app, host='0.0.0.0', port=5001, debug=debug)
