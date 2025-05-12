import sqlite3

def check_db_structure():
    conn = sqlite3.connect('instance/books.db')
    cursor = conn.cursor()
    
    # Get table info
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='user';")
    table_info = cursor.fetchone()
    print("User table structure:")
    print(table_info[0])
    
    conn.close()

if __name__ == '__main__':
    check_db_structure()
