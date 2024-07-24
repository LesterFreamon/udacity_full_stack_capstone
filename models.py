from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_security import UserMixin, RoleMixin

db = SQLAlchemy()

# Association table for many-to-many relationship between AppUsers and Roles
user_roles = db.Table('user_roles',
                      db.Column('appuser_id', db.Integer, db.ForeignKey('app_user.id'), primary_key=True),
                      db.Column('role_id', db.Integer, db.ForeignKey('role.id'), primary_key=True)
                      )


class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    def __repr__(self):
        return f'<Role {self.name}>'


class AppUser(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(300))
    active = db.Column(db.Boolean(), default=True)
    fs_uniquifier = db.Column(db.String(255), unique=True, nullable=False)  # Using a simple string field
    roles = db.relationship('Role', secondary=user_roles, backref=db.backref('app_users', lazy='dynamic'))

    @classmethod
    def get(cls, user_id):
        return cls.query.get(int(user_id))

    def __repr__(self):
        return f'<AppUser {self.username}>'


class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(120), nullable=False)
    filepath = db.Column(db.String(120), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    active = db.Column(db.Boolean, default=True, nullable=False)
    deleted_at = db.Column(db.DateTime, nullable=True)


class ImageSegment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_id = db.Column(db.Integer, db.ForeignKey('image.id', name='fk_image_segment_image_id'), nullable=False)
    processed_filename = db.Column(db.String(256), nullable=True)
    num_segments = db.Column(db.Integer, nullable=False)  # Storing the count of segments

    def __repr__(self):
        return f'<ImageSegment {self.processed_filename}>'


def init_roles():
    roles = ['admin', 'user']
    for role_name in roles:
        role = Role.query.filter_by(name=role_name).first()
        if not role:
            new_role = Role(name=role_name)
            db.session.add(new_role)
    db.session.commit()
