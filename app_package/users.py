from Databases.userdb import get_db
import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


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
            hashed_password = generate_password_hash(user_data.get('password', ''))
            hashed_security_answer = generate_password_hash(
                user_data.get('security_answer', '')
            )

            db.execute(
                '''INSERT INTO users 
                (username, fullname, phone, email, password, security_question, security_answer, 
                bio, profile_picture, address, birthday, age, gender)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (
                    username,
                    user_data.get('fullname', ''),
                    user_data.get('phone', ''),
                    user_data.get('email', ''),
                    hashed_password,
                    user_data.get('password', ''),
                    user_data.get('security_question', ''),
                    user_data.get('security_answer', ''),
                    user_data.get('bio', ''),
                    user_data.get('profile_picture', ''),
                    user_data.get('address', ''),
                    user_data.get('birthday', None),
                    user_data.get('age', None),
                    user_data.get('gender', '')
                )
            )
            db.commit()
        except sqlite3.IntegrityError:
            db.rollback()
            raise ValueError("Username, phone, or email already exists.")
        finally:
            db.close()
    
    @staticmethod
    def get_user(username):
        db = get_db()
        try:
            cursor = db.execute(
                '''SELECT username, fullname, phone, email, password,
                          security_question, security_answer, bio, profile_picture,
                          address, birthday, age, gender
                   FROM users WHERE username = ?''',
                (username,)
            )
            user_row = cursor.fetchone()
            if user_row:
                return dict(user_row)
            return None
        finally:
            db.close()


    
    @staticmethod
    def update_user(username, user_data):
        if not user_data:
            return False
        
        db = get_db()
        update_fields = ', '.join([f'{key} = ?' for key in user_data.keys()])
        update_values = list(user_data.values()) + [username]

        try:
            cursor = db.execute(F'update USERS set {update_fields} WHERE username =?',update_values)
            db.commit()
            return cursor.rowcount > 0
        finally:
            db.close()
    
    @staticmethod
    def delete_user(username):
        db = get_db()
        try:
            cursor = db.execute('DELETE FROM users WHERE username = ?', (username,))
            db.commit()
            return cursor.rowcount > 0
        finally:
            db.close()
            
    @staticmethod
    def get_user_by_username_or_email(identity):
        db = get_db()
        try:
            cursor = db.execute(
                "SELECT username, email FROM users WHERE username = ? OR email = ?",
                (identity, identity)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            db.close()

    @staticmethod
    def get_user_by_username(username):
        db = get_db()
        try:
            cursor = db.execute('SELECT * FROM users WHERE username = ?', (username,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            db.close()
    
    @staticmethod
    def get_user_by_email(email):
        db = get_db()
        try:
            cursor = db.execute('SELECT * FROM users WHERE email = ?', (email,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            db.close()
