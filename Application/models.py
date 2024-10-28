from . import db  # Import db from __init__.py
from sqlalchemy import Column, Integer, String, Date, Boolean, ForeignKey, Text, PickleType
from sqlalchemy.orm import relationship
from datetime import date
from sqlalchemy.ext.mutable import MutableList

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100), nullable=False)

class Task(db.Model):
    __tablename__ = 'task'
    id = db.Column(Integer, primary_key=True)
    title = db.Column(String(100), nullable=False)
    description = db.Column(Text, nullable=True)
    department = db.Column(String(100), nullable=True)
    assigned_user_id = db.Column(Integer, ForeignKey('user.id'), nullable=True)
    assignment_date = db.Column(Date, nullable=True)
    target_date = db.Column(Date, nullable=True)
    completed = db.Column(Boolean, default=False)
    completed_date = Column(Date, nullable=True)
    edit_count = Column(Integer, default=0)
    due_date_history = db.Column(MutableList.as_mutable(PickleType), default=[])
    assigned_user = relationship('User', backref='tasks')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'department': self.department,
            'assignment_date': self.assignment_date.isoformat() if self.assignment_date else None,
            'target_date': self.target_date.isoformat() if self.target_date else None,
            'completed': self.completed,
            'completed_date': self.completed_date.isoformat() if self.completed_date else None,  # Add this line
        }
