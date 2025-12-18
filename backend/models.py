from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Event(db.Model):
    __tablename__ = 'event'
    
    event_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to allocations
    allocations = db.relationship('EventResourceAllocation', backref='event', cascade='all, delete-orphan', lazy=True)
    
    def to_dict(self):
        return {
            'event_id': self.event_id,
            'title': self.title,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'allocated_resources': [alloc.resource.to_dict() for alloc in self.allocations]
        }
    
    def __repr__(self):
        return f'<Event {self.title}>'


class Resource(db.Model):
    __tablename__ = 'resource'
    
    resource_id = db.Column(db.Integer, primary_key=True)
    resource_name = db.Column(db.String(100), nullable=False)
    resource_type = db.Column(db.String(50), nullable=False)  # room, instructor, equipment
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to allocations
    allocations = db.relationship('EventResourceAllocation', backref='resource', cascade='all, delete-orphan', lazy=True)
    
    def to_dict(self):
        return {
            'resource_id': self.resource_id,
            'resource_name': self.resource_name,
            'resource_type': self.resource_type,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Resource {self.resource_name} ({self.resource_type})>'


class EventResourceAllocation(db.Model):
    __tablename__ = 'event_resource_allocation'
    
    allocation_id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.event_id'), nullable=False)
    resource_id = db.Column(db.Integer, db.ForeignKey('resource.resource_id'), nullable=False)
    allocated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Composite unique constraint to prevent duplicate allocations
    __table_args__ = (db.UniqueConstraint('event_id', 'resource_id', name='unique_event_resource'),)
    
    def to_dict(self):
        return {
            'allocation_id': self.allocation_id,
            'event_id': self.event_id,
            'resource_id': self.resource_id,
            'allocated_at': self.allocated_at.isoformat() if self.allocated_at else None
        }
    
    def __repr__(self):
        return f'<Allocation Event:{self.event_id} Resource:{self.resource_id}>'
