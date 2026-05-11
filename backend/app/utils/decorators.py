from functools import wraps
from flask import jsonify
from flask_login import current_user
from app.models import Project, ProjectMember

# Role hierarchy: owner > admin > member > viewer
ROLE_LEVELS = {
    'owner': 4,
    'admin': 3,
    'member': 2,
    'viewer': 1
}


def get_project_role(project_id, user_id):
    """Get user's role in a project. Returns None if not a member."""
    project = Project.query.get(project_id)
    if not project:
        return None
    if project.owner_id == user_id:
        return 'owner'
    member = ProjectMember.query.filter_by(project_id=project_id, user_id=user_id).first()
    return member.role if member else None


def has_project_access(project_id, user_id, required_role='member'):
    """Check if user has at least the required role in a project."""
    user_role = get_project_role(project_id, user_id)
    if not user_role:
        return False
    return ROLE_LEVELS.get(user_role, 0) >= ROLE_LEVELS.get(required_role, 0)


def require_project_role(role):
    """Decorator to require a minimum project role."""
    def decorator(f):
        @wraps(f)
        def decorated_function(project_id, *args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({'error': 'Authentication required'}), 401

            if not has_project_access(project_id, current_user.id, role):
                return jsonify({'error': f'{role.capitalize()} access required'}), 403

            return f(project_id, *args, **kwargs)
        return decorated_function
    return decorator


def require_project_owner(f):
    """Decorator to require project owner."""
    @wraps(f)
    def decorated_function(project_id, *args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401

        project = Project.query.get(project_id)
        if not project:
            return jsonify({'error': 'Project not found'}), 404

        if project.owner_id != current_user.id:
            return jsonify({'error': 'Owner access required'}), 403

        return f(project_id, *args, **kwargs)
    return decorated_function
