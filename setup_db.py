from app import app, db
from models import User, ReadBook, UserPreference
import os

def setup_database():
    # Make sure instance folder exists
    if not os.path.exists('instance'):
        os.makedirs('instance')
    
    db_path = os.path.join('instance', 'data.db')
    
    # Try to remove existing database if it exists
    try:
        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"Removed existing database: {db_path}")
    except Exception as e:
        print(f"Warning: Could not remove existing database: {e}")
    
    # Initialize fresh database
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        
        # Test user creation
        try:
            test_user = User(
                username='admin',
                email='admin@example.com'
            )
            test_user.set_password('admin123')
            
            db.session.add(test_user)
            db.session.commit()
            print("Successfully created test user 'admin'")
            
        except Exception as e:
            print(f"Error creating test user: {e}")
            db.session.rollback()
        
        print("Database setup complete!")

if __name__ == '__main__':
    setup_database()
