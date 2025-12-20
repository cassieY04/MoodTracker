from flask import Blueprint, render_template, session, redirect, url_for
import sqlite3
from datetime import datetime
import calendar
from Databases.emologdb import get_db
from .logemotion import EMOTION_MAP

mood_calendar_bp = Blueprint('mood_calendar', __name__)

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
            day_key = row['day'] # Returns '01', '02', etc.
            emotion = row['emotion_name']
            style = EMOTION_MAP.get(emotion, {'color': '#CCCCCC', 'emoji': '🤷'})
            
            entry = {
                'emotion': emotion,
                'note': row['note'],
                'timestamp': row['timestamp'],
                'emoji': style['emoji'] # Added emoji here
            }
            
            # Structure matches template: mood_data['01']['entries']
            if day_key not in mood_data:
                mood_data[day_key] = {'entries': []}
                
            mood_data[day_key]['entries'].append(entry)
            
        return mood_data
        
    except sqlite3.Error as e:
        print(f'Error retrieving monthly mood logs: {e}')
        return {}
    finally:
        db.close()

def get_monthly_emotion_counts(username, year, month):
    # ... (Logic reused from your previous code, placed here for organization)
    db = get_db()
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)
        
    try:
        query = """
            SELECT emotion_name, COUNT(*) as count
            FROM emolog
            WHERE username = ? AND timestamp >= ? AND timestamp < ?
            GROUP BY emotion_name
            ORDER BY count DESC
        """
        results = db.execute(query, (username, start_date.strftime('%Y-%m-%d %H:%M:%S'), end_date.strftime('%Y-%m-%d %H:%M:%S'))).fetchall()
        
        counts = []
        for row in results:
            emotion = row['emotion_name']
            style = EMOTION_MAP.get(emotion, {'color': '#CCCCCC', 'emoji': '🤷'})
            counts.append({
                'emotion': emotion,
                'count': row['count'],
                'emoji': style['emoji'],
                'color': style['color']
            })
            
        return counts
    except sqlite3.Error as e:
        print(f'Error retrieving emotion counts: {e}')
        return []
    finally:
        db.close()

@mood_calendar_bp.route("/mood_calendar")
@mood_calendar_bp.route("/mood_calendar/<int:year>/<int:month>")
def mood_calendar(year=None, month=None):
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    username = session['username']
    
    now = datetime.now()
    if year is None or month is None:
        year = now.year
        month = now.month
        
    # Ensure month is valid logic
    if month < 1:
        month = 12
        year -= 1
    elif month > 12:
        month = 1
        year += 1
        
    # Calendar navigation logic
    prev_month = month - 1
    prev_year = year
    if prev_month < 1:
        prev_month = 12
        prev_year -= 1
        
    next_month = month + 1
    next_year = year
    if next_month > 12:
        next_month = 1
        next_year += 1
        
    # Get data
    mood_data = get_monthly_mood_data(username, year, month)
    emotion_counts = get_monthly_emotion_counts(username, year, month)
    
    # Calculate summary
    total_entries = sum(item['count'] for item in emotion_counts)
    most_frequent = emotion_counts[0]['emotion'] if emotion_counts else "N/A"
        
    mood_summary = {
        'total_entries': total_entries,
        'most_frequent': most_frequent
    }
    
    # Generate calendar matrix
    cal = calendar.monthcalendar(year, month)
    month_name = calendar.month_name[month]
    
    return render_template(
        "mood_calendar.html",
        calendar=cal,
        mood_data=mood_data,
        mood_summary=mood_summary,
        emotion_counts=emotion_counts,
        year=year,
        month=month,
        month_name=month_name,
        prev_year=prev_year,
        prev_month=prev_month,
        next_year=next_year,
        next_month=next_month
    )