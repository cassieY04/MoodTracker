import sqlite3
import os

DB_NAME = "user.db"

def get_db():
    return sqlite3.connect(DB_NAME)

def init_db():
    if not os.path.exists(DB_NAME):
        db = get_db()
        cursor = db.cursor()

        cursor.execute("""
        CREATE TABLE users (
            username TEXT PRIMARY KEY,
            surname TEXT,
            lastname TEXT,
            phone TEXT UNIQUE,
            email TEXT UNIQUE,
            password TEXT,
            security_question TEXT,
            security_answer TEXT,
            bio TEXT,
            profile_picture TEXT,
            address TEXT,
            birthday DATE,
            age INTEGER,
            gender TEXT
        )
        """)

        db.commit()
        db.close()
