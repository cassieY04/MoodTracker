from Databases.userdb import get_db
import sqlite3

class UserManager:
    @staticmethod
    def user_exists(username):
        db = get_db()
        try:
            cursor = db.execute('SELECT 1 FROM users WHERE username = ?', (username,))
            return cursor.fetchone() is not None
        finally:
            db.close()
    
    @staticmethod
    def add_user(username, user_data):
        db = get_db()
        try:
            db.execute(
                'INSERT INTO users (username, phone, email, password) VALUES (?, ?, ?, ?)',
                (username, user_data['phone'], user_data['email'], user_data['password'])
            )
            db.commit()
        except sqlite3.IntegrityError:
            db.rollback()
            raise ValueError('Username or Email already exist.')
        finally:
            db.close()
        
    
    @staticmethod
    def get_user(username):
        db = get_db()
        try:
            cursor = db.execute('SELECT username, password FROM users WHERE username = ?')
            user_row = cursor.fetchone()
            if user_row:
                return dict(user_row)
            return None
        finally:
            db.close()

    
    @staticmethod
    def update_user(username, user_data):
        if username in users:
            users[username].update(user_data)
    
    @staticmethod
    def delete_user(username):
        if username in users:
            del users[username]