from Databases.userdb import get_db
import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import time

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
            
            db.execute(
                '''INSERT INTO users 
                (username, fullname, phone, email, password, security_question, security_answer, 
                bio, profile_picture, address, birthday, age, gender, failed_attempts, locked_until)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0)''',
                (
                    username,
                    user_data.get('fullname', ''),
                    user_data.get('phone', ''),
                    user_data.get('email', ''),
                    hashed_password,
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
                          address, birthday, age, gender, failed_attempts, locked_until
                   FROM users WHERE username = ?''',
                (username,)
            )
            user_row = cursor.fetchone()
            return dict(user_row)if user_row else None 
        finally:
            db.close()


    @staticmethod
    def update_user(username, user_data):
        if not user_data:
            return False
        
        db = get_db()
        
        if "password" in user_data:
            user_data["password"] = generate_password_hash(user_data["password"])

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
                "SELECT username, email , phone, password, bio, address, birthday, age, gender, security_question, security_answer, profile_picture FROM users WHERE username = ? OR email = ?",
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

    @staticmethod
    def get_failed_attempts(username):
        db = get_db()
        try:
            row = db.execute("SELECT failed_attempts FROM users WHERE username=?", (username,)).fetchone()
            return row["failed_attempts"] if row else 0
        finally:
            db.close()
    
    @staticmethod
    def increment_failed_attempts(username):
        db = get_db()
        try:
            db.execute("UPDATE users SET failed_attempts = failed_attempts + 1 WHERE username=?", (username,))
            db.commit()
        finally:
            db.close()
    
    @staticmethod
    def reset_failed_attempts(username):
        db = get_db()
        try:
            db.execute("UPDATE users SET failed_attempts = 0 WHERE username=?", (username,))
            db.commit()
        finally:
            db.close()
    
    @staticmethod
    def set_lock(username, seconds=10):
        locked_until = int(time.time()) + seconds
        db = get_db()
        try:
            db.execute("UPDATE users SET locked_until=? WHERE username=?", (locked_until, username))
            db.commit()
        finally:
            db.close()
    
    @staticmethod
    def is_locked(username):
        db = get_db()
        try:
            row = db.execute("SELECT locked_until FROM users WHERE username=?", (username,)).fetchone()
            if not row:
                return False
            return int(time.time()) < row["locked_until"]
        finally:
            db.close()

    @staticmethod
    def get_emotion_logs(username):
        db = get_db()
        try:
            cursor = db.execute('SELECT * FROM emolog WHERE username = ? ORDER BY timestamp DESC', (username,))
            return [dict(row) for row in cursor.fetchall()]
        finally:
            db.close()

    @staticmethod
    def log_emotion(username, emotion, note, thought, ai_short, ai_full, timestamp):
        db = get_db()
        try:
            db.execute("""
                INSERT INTO emolog (username, emotion_name, note, thought, ai_short_feedback, ai_full_feedback, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (username, emotion, note, thought, ai_short, ai_full, timestamp))
            db.commit()
            return True
        finally:
            db.close()

    @staticmethod
    def update_emotion_log(log_id, username, emotion, note, thought, timestamp):
        db = get_db()
        try:
            db.execute("""
                UPDATE emolog 
                SET emotion_name = ?, note = ?, thought = ?, timestamp = ? 
                WHERE id = ? AND username = ?
            """, (emotion, note, thought, timestamp, log_id, username))
            db.commit()
            return True
        finally:
            db.close()
    
    @staticmethod
    def delete_emotion_log(log_id, username):
        db = get_db()
        try:
            # Using username as a secondary check for security
            db.execute("DELETE FROM emolog WHERE id = ? AND username = ?", (log_id, username))
            db.commit()
            return True
        finally:
            db.close()