from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Task, Project, ProjectMember
from app.utils.decorators import has_project_access

bp = Blueprint('tasks', __name__, url_prefix='/api')


def _apply_task_status(task, status):
    task.status = status

    if status == 'completed':
        if not task.completed_at:
            task.completed_at = datetime.utcnow()
    else:
        task.completed_at = None


@bp.route('/projects/<int:project_id>/tasks', methods=['GET'])
@login_required
def list_tasks(project_id):
    project = Project.query.get_or_404(project_id)
    if not has_project_access(project_id, current_user.id, 'viewer'):
        return jsonify({'error': 'Access denied'}), 403

    tasks = Task.query.filter_by(project_id=project_id).all()
    return jsonify({'tasks': [t.to_dict() for t in tasks]})


@bp.route('/projects/<int:project_id>/tasks', methods=['POST'])
@login_required
def create_task(project_id):
    project = Project.query.get_or_404(project_id)
    if not has_project_access(project_id, current_user.id, 'member'):
        return jsonify({'error': 'Member access required to create tasks'}), 403

    data = request.get_json()
    if not data or not data.get('title'):
        return jsonify({'error': 'Task title is required'}), 400

    assignee_id = data.get('assignee_id')
    if assignee_id:
        if not has_project_access(project_id, assignee_id, 'viewer'):
            return jsonify({'error': 'Assignee must be a project member'}), 400

    task = Task(
        project_id=project_id,
        title=data['title'],
        description=data.get('description'),
        assignee_id=assignee_id,
        created_by=current_user.id
    )
    if assignee_id:
        task.status = 'in_progress'

    db.session.add(task)
    db.session.commit()

    return jsonify({'message': 'Task created', 'task': task.to_dict()}), 201


@bp.route('/tasks/<int:task_id>', methods=['GET'])
@login_required
def get_task(task_id):
    task = Task.query.get_or_404(task_id)
    if not has_project_access(task.project_id, current_user.id, 'viewer'):
        return jsonify({'error': 'Access denied'}), 403
    return jsonify({'task': task.to_dict()})


@bp.route('/tasks/<int:task_id>', methods=['PUT'])
@login_required
def update_task(task_id):
    task = Task.query.get_or_404(task_id)
    if not has_project_access(task.project_id, current_user.id, 'member'):
        return jsonify({'error': 'Member access required'}), 403

    data = request.get_json()

    # Only assignee can change status
    if 'status' in data:
        if task.assignee_id != current_user.id and task.project.owner_id != current_user.id:
            return jsonify({'error': 'Only assignee can change task status'}), 403
        _apply_task_status(task, data['status'])

    # Title/description can be changed by any member
    if 'title' in data:
        task.title = data['title']
    if 'description' in data:
        task.description = data['description']
    if 'assignee_id' in data:
        # Only owner/admin can reassign
        if has_project_access(task.project_id, current_user.id, 'admin'):
            task.assignee_id = data['assignee_id']

    db.session.commit()
    return jsonify({'message': 'Task updated', 'task': task.to_dict()})


@bp.route('/tasks/<int:task_id>', methods=['DELETE'])
@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.created_by != current_user.id and task.project.owner_id != current_user.id:
        return jsonify({'error': 'Only task creator or project owner can delete task'}), 403

    db.session.delete(task)
    db.session.commit()
    return jsonify({'message': 'Task deleted'})


@bp.route('/tasks/<int:task_id>/claim', methods=['POST'])
@login_required
def claim_task(task_id):
    task = Task.query.get_or_404(task_id)
    if not has_project_access(task.project_id, current_user.id, 'member'):
        return jsonify({'error': 'Member access required'}), 403
    if task.assignee_id:
        return jsonify({'error': 'Task already assigned'}), 400
    if task.status == 'completed':
        return jsonify({'error': 'Completed tasks cannot be claimed'}), 400

    task.assignee_id = current_user.id
    _apply_task_status(task, 'in_progress')
    db.session.commit()
    return jsonify({'message': 'Task claimed', 'task': task.to_dict()})


@bp.route('/tasks/<int:task_id>/complete', methods=['POST'])
@login_required
def complete_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.assignee_id != current_user.id and task.project.owner_id != current_user.id:
        return jsonify({'error': 'Only assignee or owner can complete task'}), 403

    _apply_task_status(task, 'completed')
    db.session.commit()
    return jsonify({'message': 'Task completed', 'task': task.to_dict()})
