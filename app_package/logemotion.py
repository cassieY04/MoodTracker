from flask import Blueprint, render_template, session, redirect, url_for, flash
import sqlite3
from Databases.userdb import get_db
from datetime import datetime

@staticmethod
def save_emolog(username, emotion, note):
    db = get_db()
    try:
        db.execute('''INSERT INTO emolog 
                   (username, emotion, note)
                   VALUES (?, ?, ?)'''
                   (username, emotion, note)
        )
        db.commit()
        return True
    
    except sqlite3.Error as e:
        db.rollback()
        print(f'Error saving emotion log: {e}')
        return False
    
    finally:
        db.close()

log_emotion_bp = Blueprint('log_emotion', __name__)

emotions = ['Happy', 'Sad', 'Anxious', 'Angry', 'Excited', 'Neutral', 'Stressed']

@log_emotion_bp.route("/log_emotion")
def log_emotion():
    return render_template("log_emotion.html")