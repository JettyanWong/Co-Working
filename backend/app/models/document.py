from datetime import datetime
from app import db


class Document(db.Model):
    __tablename__ = 'documents'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.LargeBinary)  # Yjs CRDT binary
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    cells = db.relationship('DocumentCell', backref='document', lazy='dynamic', cascade='all, delete-orphan')
    owner = db.relationship('User', backref='documents')

    def to_dict(self):
        project_name = None
        if self.project_id and self.project:
            project_name = self.project.name
        return {
            'id': self.id,
            'project_id': self.project_id,
            'project_name': project_name,
            'title': self.title,
            'owner_id': self.owner_id,
            'owner': self.owner.username if self.owner else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class DocumentCell(db.Model):
    __tablename__ = 'document_cells'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=False)
    cell_type = db.Column(db.Enum('code', 'text', 'image'), nullable=False)
    cell_order = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'document_id': self.document_id,
            'cell_type': self.cell_type,
            'cell_order': self.cell_order,
            'content': self.content,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
