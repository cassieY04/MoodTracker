from flask import Blueprint, render_template, session, redirect, url_for, flash, request
import sqlite3
from Databases.emologdb import get_db
from datetime import datetime
import calendar

emotion_choice = ['Happy', 'Sad', 'Anxious', 'Angry', 'Excited', 'Neutral', 'Stressed']
EMOTION_MAP = {
    'Happy': {'color': '#FFD700', 'emoji': '😊'},      # YELLOW
    'Excited': {'color': "#FFA07A", 'emoji': '🤩'},    # BEIGE
    'Neutral': {'color': '#D3D3D3', 'emoji': '😐'},    # GRAY
    'Anxious': {'color': "#F58D16", 'emoji': '😟'},    # ORANGE
    'Sad': {'color': '#000080', 'emoji': '😥'},        # NAVY BLUE
    'Angry': {'color': '#FF4500', 'emoji': '😡'},      # RED
    'Stressed': {'color': '#800080', 'emoji': '😩'},   # PURPLE
}

def get_emotion_styling(emotion):
    """Returns color and emoji for a given emotion."""
    return EMOTION_MAP.get(emotion, {'color': '#CCCCCC', 'emoji': '🤷'})

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

def get_monthly_mood_data(username, year, month):
    db = get_db()
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)

    try:
        query = """
            SELECT 
                CAST(strftime('%d', timestamp) AS INTEGER) AS day, 
                emotion_name, 
                note,
                timestamp
            FROM 
                emolog
            WHERE 
                username = ? AND 
                timestamp >= ? AND 
                timestamp < ?
            ORDER BY
                timestamp DESC
        """
        results = db.execute(query, (username, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))).fetchall()
        
        mood_data = {}
        for row in results:
            day = row['day']
            if day not in mood_data: 
                mood_data[day] = {
                    'emotion': row['emotion_name'],
                    'note': row['note'],
                    'timestamp': row['timestamp']
                }
        return mood_data
        
    except sqlite3.Error as e:
        print(f'Error retrieving monthly mood logs: {e}')
        return {}
    finally:
        db.close()

log_emotion_bp = Blueprint('log_emotion', __name__)

@log_emotion_bp.route("/log_emotion", methods=['GET', 'POST'])
def emolog():

    if 'username' not in session:
            flash('You must be logged in to log an emotion.', 'warning')
            return redirect(url_for('auth.login'))
        
    username = session['username']
    
    if request.method == 'POST':
        selected_emotion = request.form.get('emotion')
        note = request.form.get('note', '').strip()

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