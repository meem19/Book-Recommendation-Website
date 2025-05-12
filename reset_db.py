from app import db, app
import sqlite3
import os

def reset_database():
    db_path = 'instance/data.db'
    users_data = []
    preferences = []
    books_read = []
    
    # Get existing data
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        # Get existing users
        if ('user',) in tables:
            cursor.execute('SELECT * FROM user')
            users_data = cursor.fetchall()
        
        # Get user preferences
        if ('user_preference',) in tables:
            cursor.execute('SELECT user_id, category FROM user_preference')
            preferences = cursor.fetchall()
        
        # Get books read
        if ('read_book',) in tables:
            cursor.execute('SELECT user_id, book_title FROM read_book')
            books_read = cursor.fetchall()
        
        conn.close()
        
        # Delete the old database
        os.remove(db_path)
    
    # Create new database with updated schema
    with app.app_context():
        db.create_all()
    
    if users_data:
        # Reconnect to new database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Restore users
        for user in users_data:
            cursor.execute(
                'INSERT INTO user (id, username, email, password_hash, profile_pic, created_at) VALUES (?, ?, ?, ?, ?, ?)',
                user
            )
        
        # Restore preferences
        for user_id, category in preferences:
            cursor.execute(
                'INSERT INTO user_preference (user_id, category) VALUES (?, ?)',
                (user_id, category)
            )
        
        # Restore books read
        for user_id, book_title in books_read:
            cursor.execute(
                'INSERT INTO read_book (user_id, book_title, status) VALUES (?, ?, ?)',
                (user_id, book_title, 'read')
            )
        
        conn.commit()
        conn.close()
    
    print("Database reset successfully with new schema!")

if __name__ == '__main__':
    reset_database()
