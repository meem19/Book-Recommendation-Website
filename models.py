from flask_login import UserMixin
from datetime import datetime
from database import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    gender = db.Column(db.String(20))  # 'male', 'female', or 'other'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Relationships
    read_books = db.relationship('ReadBook', backref='user', lazy=True)
    preferences = db.relationship('UserPreference', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class ReadBook(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_title = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), default='read')  # read, reading, want_to_read
    rating = db.Column(db.Integer)  # 1-5 stars
    review = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class UserPreference(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    weight = db.Column(db.Float, default=1.0)  # How much user likes this category
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
