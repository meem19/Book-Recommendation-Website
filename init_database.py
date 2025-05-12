from app import app, db
from models import User, ReadBook, UserPreference
import os

def init_database():
    # Make sure instance folder exists
    if not os.path.exists('instance'):
        os.makedirs('instance')
    
    # Initialize database without dropping existing tables
    with app.app_context():
        # Only create tables that don't exist
        db.create_all()
        print("Database initialized successfully!")

if __name__ == '__main__':
    init_database()
