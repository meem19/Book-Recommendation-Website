from app import app, db
import sqlite3

def add_profile_pic():
    try:
        # First ensure database exists with tables
        with app.app_context():
            db.create_all()
        
        # Connect to the database
        conn = sqlite3.connect('instance/books.db')
        cursor = conn.cursor()
        
        # Add the profile_pic column
        cursor.execute('ALTER TABLE user ADD COLUMN profile_pic VARCHAR(10) DEFAULT "male"')
        
        # Commit the changes
        conn.commit()
        print("Successfully added profile_pic column!")
        
    except sqlite3.OperationalError as e:
        print(f"Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    add_profile_pic()
