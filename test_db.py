from app import app, db
from models import User
from werkzeug.security import generate_password_hash

def test_database():
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()
        
        # Try to add a test user
        test_user = User(
            username='testuser',
            email='test@example.com',
            password_hash=generate_password_hash('password123')
        )
        
        try:
            db.session.add(test_user)
            db.session.commit()
            print("Successfully added test user!")
            
            # Verify user was added
            user = User.query.filter_by(username='testuser').first()
            if user:
                print(f"Found user: {user.username} with email: {user.email}")
            else:
                print("Could not find test user in database!")
                
        except Exception as e:
            print(f"Error adding user: {e}")
            db.session.rollback()

if __name__ == '__main__':
    test_database()
