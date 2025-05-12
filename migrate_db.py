from app import db, app
import sqlite3
import os

def migrate_database():
    # Get the database path
    db_path = 'instance/data.db'
    
    if not os.path.exists(db_path):
        print(f"Database file {db_path} does not exist")
        return
    
    # Connect to SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Add the gender column if it doesn't exist
        cursor.execute("PRAGMA table_info(user)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'gender' not in columns:
            cursor.execute('ALTER TABLE user ADD COLUMN gender VARCHAR(20)')
            # Set default gender as 'other' for existing users
            cursor.execute('UPDATE user SET gender = ?', ('other',))
            conn.commit()
            print("Successfully added gender column and set default values")
        else:
            print("Gender column already exists")
            
    except sqlite3.OperationalError as e:
        print(f"Error during migration: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    migrate_database()
