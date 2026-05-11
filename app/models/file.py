from datetime import datetime
from app import db
import os


class File(db.Model):
    __tablename__ = 'files'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=True)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(500), nullable=False)
    size = db.Column(db.Integer)  # bytes
    uploader_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    uploader = db.relationship('User', backref='uploaded_files')

    def to_dict(self):
        project_name = None
        if self.project_id and self.project:
            project_name = self.project.name
        return {
            'id': self.id,
            'project_id': self.project_id,
            'project_name': project_name,
            'filename': self.filename,
            'size': self.size,
            'uploader_id': self.uploader_id,
            'uploader': self.uploader.username if self.uploader else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
