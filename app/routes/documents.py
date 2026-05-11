from flask import Blueprint, request, jsonify, Response
from flask_login import login_required, current_user
from app import db
from app.models import Document, DocumentCell, Task, Project
from app.utils.decorators import has_project_access
from app.services.collab import persist_ydoc
import base64

bp = Blueprint('documents', __name__, url_prefix='/api/documents')


@bp.route('', methods=['GET'])
@login_required
def list_documents():
    """List all documents visible to the current user."""
    from app.models import ProjectMember
    # Owned documents
    owned = Document.query.filter_by(owner_id=current_user.id).all()
    # Documents in projects where user is a member
    project_ids = [m.project_id for m in ProjectMember.query.filter_by(user_id=current_user.id).all()]
    project_docs = Document.query.filter(Document.project_id.in_(project_ids)).all() if project_ids else []
    # Merge and deduplicate
    seen = set()
    documents = []
    for d in owned + project_docs:
        if d.id not in seen:
            seen.add(d.id)
            documents.append(d)
    return jsonify({'documents': [d.to_dict() for d in documents]})


@bp.route('', methods=['POST'])
@login_required
def create_document():
    data = request.get_json()
    if not data or not data.get('title'):
        return jsonify({'error': 'Document title is required'}), 400

    project_id = data.get('project_id')
    if project_id:
        if not has_project_access(project_id, current_user.id, 'viewer'):
            return jsonify({'error': 'Access denied'}), 403
        # Project owner always has full permissions
        project = Project.query.get(project_id)
        is_owner = project and project.owner_id == current_user.id
        if not is_owner:
            has_task = Task.query.filter_by(
                project_id=project_id, assignee_id=current_user.id
            ).first()
            if not has_task:
                return jsonify({'error': 'Only task assignees can create documents'}), 403

    document = Document(
        title=data['title'],
        project_id=project_id,
        owner_id=current_user.id
    )
    db.session.add(document)
    db.session.commit()

    return jsonify({'message': 'Document created', 'document': document.to_dict()}), 201


@bp.route('/<int:doc_id>', methods=['GET'])
@login_required
def get_document(doc_id):
    document = Document.query.get_or_404(doc_id)
    if document.project_id:
        if not has_project_access(document.project_id, current_user.id, 'viewer'):
            return jsonify({'error': 'Access denied'}), 403

    cells = DocumentCell.query.filter_by(document_id=doc_id).order_by(DocumentCell.cell_order).all()
    result = {
        'document': document.to_dict(),
        'cells': [c.to_dict() for c in cells]
    }
    # Include Yjs state if stored
    if document.content:
        result['yjs_state'] = base64.b64encode(document.content).decode('utf-8')
    return jsonify(result)


@bp.route('/<int:doc_id>', methods=['PUT'])
@login_required
def update_document(doc_id):
    document = Document.query.get_or_404(doc_id)

    # Check permission: owner OR task assignee in the project
    if document.owner_id != current_user.id:
        if document.project_id:
            if not has_project_access(document.project_id, current_user.id, 'viewer'):
                return jsonify({'error': 'Access denied'}), 403
            project = Project.query.get(document.project_id)
            is_owner = project and project.owner_id == current_user.id
            if not is_owner:
                has_task = Task.query.filter_by(
                    project_id=document.project_id, assignee_id=current_user.id
                ).first()
                if not has_task:
                    return jsonify({'error': 'Only task assignees can edit documents'}), 403
        else:
            return jsonify({'error': 'Only owner can update standalone document'}), 403

    data = request.get_json()
    if 'title' in data:
        document.title = data['title']
    if 'yjs_state' in data:
        try:
            document.content = base64.b64decode(data['yjs_state'])
        except Exception:
            pass

    # Persist server-side Yjs state too
    try:
        persist_ydoc(str(doc_id))
    except Exception:
        pass

    # Handle cells update
    if 'cells' in data:
        # Delete existing cells
        DocumentCell.query.filter_by(document_id=doc_id).delete()

        # Create new cells
        for cell_data in data['cells']:
            cell = DocumentCell(
                document_id=doc_id,
                cell_type=cell_data.get('cell_type', 'text'),
                cell_order=cell_data.get('cell_order', 0),
                content=cell_data.get('content', '')
            )
            db.session.add(cell)

    db.session.commit()
    return jsonify({'message': 'Document updated', 'document': document.to_dict()})


@bp.route('/<int:doc_id>', methods=['DELETE'])
@login_required
def delete_document(doc_id):
    document = Document.query.get_or_404(doc_id)
    if document.owner_id != current_user.id:
        return jsonify({'error': 'Only owner can delete document'}), 403

    db.session.delete(document)
    db.session.commit()
    return jsonify({'message': 'Document deleted'})


@bp.route('/<int:doc_id>/download', methods=['GET'])
@login_required
def download_document(doc_id):
    document = Document.query.get_or_404(doc_id)
    if document.project_id:
        if not has_project_access(document.project_id, current_user.id, 'viewer'):
            return jsonify({'error': 'Access denied'}), 403

    cells = DocumentCell.query.filter_by(document_id=doc_id).order_by(DocumentCell.cell_order).all()

    # Export as markdown-like text
    content = f"# {document.title}\n\n"
    for cell in cells:
        if cell.cell_type == 'code':
            content += f"```\n{cell.content or ''}\n```\n\n"
        else:
            content += f"{cell.content or ''}\n\n"

    return Response(content, mimetype='text/plain', headers={
        'Content-Disposition': f'attachment; filename={document.title}.md'
    })
