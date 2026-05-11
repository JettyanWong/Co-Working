from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import User, Project, Task, Document, File
from functools import wraps

bp = Blueprint('users', __name__, url_prefix='/api/users')


def admin_required(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if current_user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated


@bp.route('', methods=['GET'])
@login_required
@admin_required
def list_users():
    users = User.query.all()
    return jsonify({'users': [u.to_dict() for u in users]})


@bp.route('/<int:user_id>', methods=['GET'])
@login_required
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify({'user': user.to_dict()})


@bp.route('/<int:user_id>', methods=['PUT'])
@login_required
def update_user(user_id):
    if current_user.id != user_id and current_user.role != 'admin':
        return jsonify({'error': 'Permission denied'}), 403

    user = User.query.get_or_404(user_id)
    data = request.get_json()

    if 'email' in data:
        user.email = data['email']
    if current_user.role == 'admin':
        if 'role' in data:
            user.role = data['role']
        if 'status' in data:
            user.status = data['status']

    db.session.commit()
    return jsonify({'message': 'User updated', 'user': user.to_dict()})


@bp.route('/<int:user_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    # Clean up all related records before deleting user
    Project.query.filter_by(owner_id=user_id).delete()
    Document.query.filter_by(owner_id=user_id).delete()
    File.query.filter_by(uploader_id=user_id).delete()
    Task.query.filter_by(created_by=user_id).delete()
    # Clear assignee references (nullable FK)
    Task.query.filter_by(assignee_id=user_id).update({'assignee_id': None})
    # Remove project memberships
    from app.models import ProjectMember
    ProjectMember.query.filter_by(user_id=user_id).delete()
    db.session.flush()
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'User deleted'})


@bp.route('/<int:user_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_user(user_id):
    user = User.query.get_or_404(user_id)
    user.status = 'active'
    db.session.commit()
    return jsonify({'message': 'User approved', 'user': user.to_dict()})


@bp.route('/<int:user_id>/reject', methods=['POST'])
@login_required
@admin_required
def reject_user(user_id):
    user = User.query.get_or_404(user_id)
    # Only delete pending users (safety check)
    if user.status != 'pending':
        return jsonify({'error': 'Can only reject pending users'}), 400
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'User rejected and removed'})
