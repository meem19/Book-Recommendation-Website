from app import app, db
from models import User
import os
import sqlite3

def fix_database():
    instance_dir = 'instance'
    db_path = os.path.join(instance_dir, 'data.db')
    
    print(f"Checking database at: {db_path}")
    
    # Create instance directory if it doesn't exist
    if not os.path.exists(instance_dir):
        os.makedirs(instance_dir)
        print(f"Created directory: {instance_dir}")
    
    # Try to connect to the database
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if user table exists and its structure
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='user';")
        result = cursor.fetchone()
        
        if result:
            print("Current user table schema:")
            print(result[0])
        else:
            print("User table does not exist")
        
        conn.close()
        
    except Exception as e:
        print(f"Error checking database: {e}")
    
    # Initialize database with Flask-SQLAlchemy
    with app.app_context():
        try:
            print("\nCreating all tables...")
            db.create_all()
            print("Tables created successfully")
            
            # Try to add a test user
            test_user = User(
                username='testadmin',
                email='testadmin@example.com'
            )
            test_user.set_password('admin123')
            
            db.session.add(test_user)
            db.session.commit()
            print("Successfully added test user!")
            
            # Verify the user was added
            users = User.query.all()
            print(f"\nUsers in database: {len(users)}")
            for user in users:
                print(f"- {user.username} ({user.email})")
            
        except Exception as e:
            print(f"Error: {e}")
            db.session.rollback()

if __name__ == '__main__':
    fix_database()
