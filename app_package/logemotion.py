from flask import Blueprint, render_template, session, redirect, url_for, flash, request
import sqlite3
from Databases.emologdb import get_db
from datetime import datetime

@staticmethod
def save_emolog(username, emotion, note):
    db = get_db()
    try:
        db.execute('''INSERT INTO emolog 
                   (username, emotion_name, note)
                   VALUES (?, ?, ?)''',
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

emotion_choice = ['Happy', 'Sad', 'Anxious', 'Angry', 'Excited', 'Neutral', 'Stressed']

@log_emotion_bp.route("/log_emotion", methods=['GET', 'POST'])
def emolog():
    if request.method == 'POST':
        selected_emotion = request.form.get('emotion')
        note = request.form.get('note', '').strip()
        username = session['username']

        if not selected_emotion or selected_emotion not in emotion_choice:
            flash('Please select a valid emotion.', 'error')
            return redirect(url_for('log_emotion.emolog'))
        
        if save_emolog(username, selected_emotion, note):
            if selected_emotion in ['Happy', 'Excited']:
                flash(f"🎉 Log Saved! Great to see you feeling {selected_emotion}!", "success")
            else:
                flash(f"🫂 Log Saved. We noted you felt {selected_emotion}.", "info")
            return redirect(url_for('log_emotion.emolog'))
        
        else:
            flash("An error occurred while saving the log. Check the console.", "error")
            return redirect(url_for("log_emotion.emolog"))

    return render_template("log_emotion.html", emotions = emotion_choice)