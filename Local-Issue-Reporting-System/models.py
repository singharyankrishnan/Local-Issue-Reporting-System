from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


from app import db
class Issue(db.Model):
    """Model for storing civic issues reported by citizens"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(200), nullable=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    photo_filename = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(20), default='submitted', nullable=False)
    priority = db.Column(db.String(20), default='medium', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    admin_notes = db.Column(db.Text)
    assigned_to = db.Column(db.String(100))
    authority_notified = db.Column(db.Boolean, default=False, nullable=False)
    notification_sent_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<Issue {self.id}: {self.category} - {self.status}>'

    def to_dict(self):
        """Convert issue to dictionary for easy JSON serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'category': self.category,
            'description': self.description,
            'location': self.location,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'photo_filename': self.photo_filename,
            'status': self.status,
            'priority': self.priority,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
            'admin_notes': self.admin_notes,
            'assigned_to': self.assigned_to,
            'authority_notified': self.authority_notified,
            'notification_sent_at': self.notification_sent_at.strftime('%Y-%m-%d %H:%M:%S') if self.notification_sent_at else None
        }

class Admin(UserMixin, db.Model):
    """Model for admin users"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    role = db.Column(db.String(20), default='admin', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    active = db.Column(db.Boolean, default=True, nullable=False)

    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if provided password matches the hash"""
        return check_password_hash(self.password_hash, password)

    def is_active(self):
        """Return whether admin account is active"""
        return self.active

    def __repr__(self):
        return f'<Admin {self.username}>'
