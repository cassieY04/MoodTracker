import sqlite3
import os
from datetime import datetime, timedelta, timezone

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'user.db')

def get_db():
    db = sqlite3.connect(
        DB_PATH,
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
                   thought TEXT,
                   ai_short_feedback TEXT,
                   ai_full_feedback TEXT,
                   timestamp TEXT, 
                   FOREIGN KEY(username) REFERENCES users(username)
            )''')
        
        #check for missing columns (migration for existing db)
        cursor = db.execute("PRAGMA table_info(emolog)")
        columns = [col['name'] for col in cursor.fetchall()]
        
        if 'ai_short_feedback' not in columns:
            db.execute("ALTER TABLE emolog ADD COLUMN ai_short_feedback TEXT")
        if 'ai_full_feedback' not in columns:
            db.execute("ALTER TABLE emolog ADD COLUMN ai_full_feedback TEXT")
        if 'thought' not in columns:
            db.execute("ALTER TABLE emolog ADD COLUMN thought TEXT")
            
        db.commit()
    
    except Exception as e:
        print(f'Error creating emolog table: {e}')
        db.rollback()
    
    finally:
        db.close()
        
def save_emolog(username, emotion, note, thought, ai_short, ai_full, timestamp):
    db = get_db()
    try:
        cursor = db.execute('''INSERT INTO emolog
                    (username, emotion_name, note, thought, ai_short_feedback, ai_full_feedback, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?)''',
                    (username, emotion, note, thought, ai_short, str(ai_full), timestamp)
        )
        db.commit()
        return cursor.lastrowid
        
    except sqlite3.Error as e:
        db.rollback()
        print(f'Error saving emotion log: {e}')
        return False
        
    finally:
        db.close()
        
def get_latest_emolog(username):
    db = get_db()
    cur = db.execute(
        "SELECT * FROM emolog WHERE username = ? ORDER BY timestamp DESC LIMIT 1",
        (username,)
    
    )
    row = cur.fetchone()
    db.close()
    return row

def get_emolog_by_id(log_id):
    db = get_db()
    try:
        cur = db.execute("SELECT * FROM emolog WHERE id = ?", (log_id,))
        row = cur.fetchone()
        return row
    finally:
        db.close()
