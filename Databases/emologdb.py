import sqlite3

def get_db():
    db = sqlite3.connect(
        'user.db',
        detect_types=sqlite3.PARSE_DECLTYPES
    )
    db.row_factory = sqlite3.Row
    return db

def init_emologdb():
    db = get_db()
    try:
        db.execute('''CREATE TABLE IF NOT EXISTS emolog (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   username TEXT NOT NULL,
                   emotion_name TEXT NOT NULL,
                   note TEXT,
                   timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                   FOREIGN KEY(username) REFERENCES users(username)
            )''')
        db.commit()
    
    except Exception as e:
        print(f'Error creating emolog table: {e}')
        db.rollback()
    
    finally:
        db.close()