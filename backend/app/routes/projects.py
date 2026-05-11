from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Project, ProjectMember, User, Document, File
from app.utils.decorators import get_project_role, has_project_access, require_project_owner

bp = Blueprint('projects', __name__, url_prefix='/api/projects')


@bp.route('', methods=['GET'])
@login_required
def list_projects():
    # Get projects where user is owner or member
    owned = Project.query.filter_by(owner_id=current_user.id).all()
    as_member = Project.query.join(ProjectMember).filter(ProjectMember.user_id == current_user.id).all()
    projects = {p.id: p for p in owned + as_member}.values()
    return jsonify({'projects': [p.to_dict() for p in projects]})


@bp.route('', methods=['POST'])
@login_required
def create_project():
    data = request.get_json()
    if not data or not data.get('name'):
        return jsonify({'error': 'Project name is required'}), 400

    project = Project(name=data['name'], description=data.get('description'), owner_id=current_user.id)
    db.session.add(project)
    db.session.flush()

    # Add owner as member
    member = ProjectMember(project_id=project.id, user_id=current_user.id, role='owner')
    db.session.add(member)

    # Add specified members
    member_ids = data.get('member_ids', [])
    for uid in member_ids:
        if uid == current_user.id:
            continue
        if not ProjectMember.query.filter_by(project_id=project.id, user_id=uid).first():
            db.session.add(ProjectMember(project_id=project.id, user_id=uid, role='member'))

    db.session.commit()
    return jsonify({'message': 'Project created', 'project': project.to_dict()}), 201


@bp.route('/<int:project_id>', methods=['GET'])
@login_required
def get_project(project_id):
    project = Project.query.get_or_404(project_id)
    if not has_project_access(project_id, current_user.id, 'viewer'):
        return jsonify({'error': 'Access denied'}), 403
    return jsonify({'project': project.to_dict()})


@bp.route('/<int:project_id>', methods=['PUT'])
@login_required
def update_project(project_id):
    project = Project.query.get_or_404(project_id)
    if not has_project_access(project_id, current_user.id, 'admin'):
        return jsonify({'error': 'Admin access required to update project'}), 403

    data = request.get_json()
    if 'name' in data:
        project.name = data['name']
    if 'description' in data:
        project.description = data['description']

    db.session.commit()
    return jsonify({'message': 'Project updated', 'project': project.to_dict()})


@bp.route('/<int:project_id>', methods=['DELETE'])
@login_required
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    if project.owner_id != current_user.id:
        return jsonify({'error': 'Only owner can delete project'}), 403

    db.session.delete(project)
    db.session.commit()
    return jsonify({'message': 'Project deleted'})


@bp.route('/<int:project_id>/members', methods=['GET'])
@login_required
def list_members(project_id):
    project = Project.query.get_or_404(project_id)
    if not has_project_access(project_id, current_user.id, 'viewer'):
        return jsonify({'error': 'Access denied'}), 403
    members = ProjectMember.query.filter_by(project_id=project_id).all()
    return jsonify({'members': [m.to_dict() for m in members]})


@bp.route('/<int:project_id>/members', methods=['POST'])
@login_required
def add_member(project_id):
    project = Project.query.get_or_404(project_id)
    if not has_project_access(project_id, current_user.id, 'admin'):
        return jsonify({'error': 'Admin access required to add members'}), 403

    data = request.get_json()
    if not data or not data.get('user_id'):
        return jsonify({'error': 'user_id is required'}), 400

    user = User.query.get_or_404(data['user_id'])
    if ProjectMember.query.filter_by(project_id=project_id, user_id=user.id).first():
        return jsonify({'error': 'User already a member'}), 400

    role = data.get('role', 'member')
    if role not in ('admin', 'member', 'viewer'):
        role = 'member'

    member = ProjectMember(project_id=project_id, user_id=user.id, role=role)
    db.session.add(member)
    db.session.commit()

    return jsonify({'message': 'Member added', 'member': member.to_dict()}), 201


@bp.route('/<int:project_id>/members/<int:user_id>', methods=['PUT'])
@login_required
def update_member_role(project_id, user_id):
    if not has_project_access(project_id, current_user.id, 'admin'):
        return jsonify({'error': 'Admin access required'}), 403

    member = ProjectMember.query.filter_by(project_id=project_id, user_id=user_id).first_or_404()

    data = request.get_json()
    new_role = data.get('role')
    if new_role in ('admin', 'member', 'viewer'):
        member.role = new_role
        db.session.commit()

    return jsonify({'message': 'Member role updated', 'member': member.to_dict()})


@bp.route('/<int:project_id>/members/<int:user_id>', methods=['DELETE'])
@login_required
def remove_member(project_id, user_id):
    project = Project.query.get_or_404(project_id)
    if project.owner_id != current_user.id:
        return jsonify({'error': 'Only owner can remove members'}), 403
    if user_id == project.owner_id:
        return jsonify({'error': 'Cannot remove owner'}), 400

    member = ProjectMember.query.filter_by(project_id=project_id, user_id=user_id).first_or_404()
    db.session.delete(member)
    db.session.commit()
    return jsonify({'message': 'Member removed'})


@bp.route('/<int:project_id>/documents', methods=['GET'])
@login_required
def list_documents(project_id):
    project = Project.query.get_or_404(project_id)
    if not has_project_access(project_id, current_user.id, 'viewer'):
        return jsonify({'error': 'Access denied'}), 403
    documents = Document.query.filter_by(project_id=project_id).all()
    return jsonify({'documents': [d.to_dict() for d in documents]})


@bp.route('/<int:project_id>/files', methods=['GET'])
@login_required
def list_files(project_id):
    project = Project.query.get_or_404(project_id)
    if not has_project_access(project_id, current_user.id, 'viewer'):
        return jsonify({'error': 'Access denied'}), 403
    files = File.query.filter_by(project_id=project_id).all()
    return jsonify({'files': [f.to_dict() for f in files]})
