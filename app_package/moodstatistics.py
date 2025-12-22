from flask import Blueprint, render_template, session, redirect, url_for, flash
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import sqlite3
import calendar
from .logemotion import get_db, get_emotion_styling, EMOTION_MAP

mood_statistics_bp = Blueprint('mood_statistics', __name__)


def get_logs_for_period(username, period='month'):
    """
    Fetches all emotion logs for the given period (default: current month).
    :param period: 'week', 'month', or 'all'
    """
    db = get_db()
    
    current_time = datetime.now()
    start_date = None
    end_date = None
    
    if period == 'week':
        start_date = current_time.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=current_time.weekday())
        end_date = start_date + timedelta(days=7)
    elif period == 'month':
        start_date = datetime(current_time.year, current_time.month, 1)
        end_date = start_date + relativedelta(months=1)
    elif period == 'all':
        start_date = datetime.min.strftime('%Y-%m-%d %H:%M:%S')
        end_date = datetime.max.strftime('%Y-%m-%d %H:%M:%S')
    else:
        return get_logs_for_period(username, 'month') 

    if period == 'all':
        date_conditions = "timestamp >= ? AND timestamp <= ?"
    else:
        date_conditions = "timestamp >= ? AND timestamp < ?"

    query = f"""
        SELECT 
            emotion_name, 
            note,
            timestamp
        FROM 
            emolog
        WHERE 
            username = ? AND 
            {date_conditions}
        ORDER BY
            timestamp ASC
    """
    
    try:
        if period != 'all':
            start_str = start_date.strftime('%Y-%m-%d %H:%M:%S')
            end_str = end_date.strftime('%Y-%m-%d %H:%M:%S')
        else:
            start_str = start_date
            end_str = end_date
        
        print(f"DEBUG: Period={period}, Start={start_str}, End={end_str}")   
       
        results = db.execute(query, (username, start_str, end_str)).fetchall()
        
        logs = [{
            'emotion': row['emotion_name'],
            'note': row['note'],
            'timestamp': row['timestamp']
        } for row in results]
        
        return logs
        
    except sqlite3.Error as e:
        print(f'Error retrieving mood logs for statistics: {e}')
        return []
    finally:
        db.close()



def analyze_logs(logs):
    if not logs:
        return {
            "total_entries": 0,
            "most_frequent": "N/A",
            "emotion_breakdown": {}
        }
        
    emotion_counts = {}
    total_entries = len(logs)

    for log in logs:
        emotion = log['emotion'] 
        emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1

    emotion_analysis = {}
    for emotion, count in emotion_counts.items():
        percentage = (count / total_entries) * 100
        styling = get_emotion_styling(emotion)
        
        emotion_analysis[emotion] = {
            'count': count,
            'percentage': round(percentage, 1),
            'color': styling['color'],
            'emoji': styling['emoji']
        }

    most_frequent = max(emotion_counts, key=emotion_counts.get) if emotion_counts else "N/A"
    
    summary = {
        'total_entries': total_entries,
        'emotion_breakdown': emotion_analysis,
        'most_frequent': most_frequent,
    }
    return summary


@mood_statistics_bp.route("/mood_statistics", methods=['GET'])
@mood_statistics_bp.route("/mood_statistics/<string:period>", methods=['GET'])
def mood_statistics_view(period='month'):
    if 'username' not in session:
        flash("Please log in to view the mood statistics.", 'warning')
        return redirect(url_for('auth.login'))
    
    username = session['username']
    
    logs = get_logs_for_period(username, period)
    
    statistics = analyze_logs(logs)
    
    if period == 'week':
        title = "Weekly Mood Summary"
    elif period == 'all':
        title = "All-Time Mood Summary"
    else:
        title = "Monthly Mood Summary"

    return render_template("mood_statistics.html",
                            period=period,
                            title=title,
                            stats=statistics,
                            all_emotions=EMOTION_MAP.keys(),
                            get_styling=get_emotion_styling 
    )