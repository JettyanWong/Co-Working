from flask import Blueprint, request, jsonify, send_file, current_app
from flask_login import login_required, current_user
from app import db
from app.models import File
from app.utils.decorators import has_project_access
from werkzeug.utils import secure_filename
import mimetypes
import os
import uuid

mimetypes.add_type('text/markdown', '.md')

bp = Blueprint('files', __name__, url_prefix='/api/files')


@bp.route('', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    project_id = request.form.get('project_id')

    if project_id:
        if not has_project_access(int(project_id), current_user.id, 'member'):
            return jsonify({'error': 'Access denied'}), 403

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    filename = secure_filename(file.filename)
    ext = filename.rsplit('.', 1)[1] if '.' in filename else ''
    unique_name = f"{uuid.uuid4().hex}.{ext}" if ext else uuid.uuid4().hex

    upload_folder = current_app.config['UPLOAD_FOLDER']
    os.makedirs(upload_folder, exist_ok=True)
    filepath = os.path.join(upload_folder, unique_name)
    file.save(filepath)
    # Store absolute path so send_file works regardless of cwd / app root_path
    filepath = os.path.abspath(filepath)

    file_record = File(
        project_id=int(project_id) if project_id else None,
        filename=filename,
        filepath=filepath,
        size=os.path.getsize(filepath),
        uploader_id=current_user.id
    )
    db.session.add(file_record)
    db.session.commit()

    return jsonify({'message': 'File uploaded', 'file': file_record.to_dict()}), 201


@bp.route('/<int:file_id>/view', methods=['GET'])
def view_file(file_id):
    if not current_user.is_authenticated:
        return jsonify({'error': 'Not authenticated'}), 401
    file_record = File.query.get_or_404(file_id)
    if file_record.project_id:
        if not has_project_access(file_record.project_id, current_user.id, 'viewer'):
            return jsonify({'error': 'Access denied'}), 403
    return send_file(file_record.filepath)


@bp.route('/<int:file_id>/download', methods=['GET'])
@login_required
def download_file(file_id):
    file_record = File.query.get_or_404(file_id)
    if file_record.project_id:
        if not has_project_access(file_record.project_id, current_user.id, 'viewer'):
            return jsonify({'error': 'Access denied'}), 403

    return send_file(file_record.filepath, as_attachment=True, download_name=file_record.filename)


@bp.route('/<int:file_id>', methods=['DELETE'])
@login_required
def delete_file(file_id):
    file_record = File.query.get_or_404(file_id)
    if file_record.uploader_id != current_user.id:
        return jsonify({'error': 'Only uploader can delete file'}), 403

    # Delete physical file
    if os.path.exists(file_record.filepath):
        os.remove(file_record.filepath)

    db.session.delete(file_record)
    db.session.commit()
    return jsonify({'message': 'File deleted'})
