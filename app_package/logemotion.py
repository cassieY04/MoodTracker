from flask import Blueprint, render_template, session, redirect, url_for, flash, request
import sqlite3
from Databases.emologdb import get_db
from datetime import datetime
import calendar
from .aifeedback import generate_ai_feedback


emotion_choice = ['Happy', 'Sad', 'Anxious', 'Angry', 'Excited', 'Neutral', 'Stressed']
EMOTION_MAP = {
    'Happy': {'color': '#FFD700', 'emoji': '😊'},      
    'Excited': {'color': "#FFA07A", 'emoji': '🤩'},     
    'Neutral': {'color': '#D3D3D3', 'emoji': '😐'},     
    'Anxious': {'color': "#F58D16", 'emoji': '😟'},     
    'Sad': {'color': '#000080', 'emoji': '😥'},         
    'Angry': {'color': '#FF4500', 'emoji': '😡'},       
    'Stressed': {'color': '#800080', 'emoji': '😩'},    
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
                CAST(strftime('%d', timestamp) AS TEXT) AS day, 
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
                timestamp ASC
        """
        results = db.execute(query, (username, start_date.strftime('%Y-%m-%d %H:%M:%S'), end_date.strftime('%Y-%m-%d %H:%M:%S'))).fetchall()
        
        mood_data = {}
        for row in results:
            day_key = row['day']
            
            entry = {
                'emotion': row['emotion_name'],
                'note': row['note'],
                'timestamp': row['timestamp']
            }
            
            # Appends all entries for a given day to a list
            if day_key not in mood_data:
                mood_data[day_key] = []
                
            mood_data[day_key].append(entry)
            
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
    feedback = None
    show_feedback = False
    
    if request.method == 'POST':
        selected_emotion = request.form.get('emotion')
        note = request.form.get('note', '').strip()
        thought = request.form.get('thought', '').strip()
        combined_note = f"{note} {thought}".strip()

        if not selected_emotion or selected_emotion not in emotion_choice:
            flash('Please select a valid emotion.', 'error')
            return redirect(url_for('log_emotion.emolog'))
        
        if save_emolog(username, selected_emotion, combined_note):
            feedback = generate_ai_feedback(selected_emotion, combined_note)
            show_feedback = True
            flash('Emotion log saved successfully!', 'success')
            # We will now render the page again with the feedback
        else:
            flash("An error occurred while saving the log. Check the console.", "error")
            # Let the function fall through to render the template

    return render_template("log_emotion.html", emotions = emotion_choice, aifeedback=feedback, show_feedback=show_feedback)