import sqlite3

DATABASE = 'user.db'

def get_db(): #return a connection object to database
    db = sqlite3.connect(
        DATABASE,
        detect_types=sqlite3.PARSE_DECLTYPES
    )

    db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()

    db.execute('''CREATE TABLE IF NOT EXISTS users (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               username TEXT NOT NULL UNIQUE,
               surname TEXT NOT NULL,
               lastname TEXT NOT NULL,
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
                gender TEXT
            )''')

    db.commit()
    db.close()