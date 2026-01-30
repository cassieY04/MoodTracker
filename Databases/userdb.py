import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'user.db')

def get_db(): #return a connection object to database
    db = sqlite3.connect(
        DB_PATH,
        detect_types=sqlite3.PARSE_DECLTYPES
    )

    db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    try:
        db.execute('''CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                fullname TEXT NOT NULL,
                phone TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                security_question TEXT NOT NULL,
                security_answer TEXT NOT NULL,
                bio TEXT,
                profile_picture TEXT,
                address TEXT,
                birthday DATE,
                age INTEGER,
                gender TEXT,
                failed_attempts INTEGER DEFAULT 0,
                locked_until INTEGER DEFAULT 0,
                theme TEXT DEFAULT 'light'
            )''')

        db.commit()

    except Exception as e:
        print(f"Error creating user table: {e}")
        db.rollback()

    finally:
        db.close()