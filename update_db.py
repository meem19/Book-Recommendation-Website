from app import app, db
from models import User
from sqlalchemy import text
import os

def update_database():
    # Make sure instance folder exists
    if not os.path.exists('instance'):
        os.makedirs('instance')
    
    with app.app_context():
        # Add the column using raw SQL
        try:
            db.session.execute(text('ALTER TABLE user ADD COLUMN profile_pic VARCHAR(10) DEFAULT "male"'))
            db.session.commit()
            print("Successfully added profile_pic column!")
        except Exception as e:
            if 'duplicate column name' in str(e):
                print("Profile pic column already exists")
            else:
                print(f"Error: {e}")
                db.session.rollback()

if __name__ == '__main__':
    update_database()
