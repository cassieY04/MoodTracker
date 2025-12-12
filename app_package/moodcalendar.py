from flask import Blueprint, render_template, session, redirect, url_for, flash
from datetime import datetime
import calendar
from .logemotion import get_monthly_mood_data, get_emotion_styling

mood_calendar_bp = Blueprint('mood_calendar', __name__)

def calculate_mood_summary(processed_data):
    if not processed_data:
        return {"total_entries": 0, "most_frequent": "N/A", "emotion_breakdown": {}}
        
    emotion_counts = {}
    total_entries = 0

    for day in processed_data:
        day_data = processed_data[day]
        total_entries += day_data['total_entries']
        
        for entry in day_data['entries']:
            emotion = entry['emotion']
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1

    most_frequent = max(emotion_counts, key=emotion_counts.get) if emotion_counts else "N/A"
    
    summary = {
        'total_entries': total_entries,
        'emotion_breakdown': emotion_counts,
        'most_frequent': most_frequent,
    }
    return summary
        
    

@mood_calendar_bp.route("/mood_calendar", methods=['GET'])
@mood_calendar_bp.route("/mood_calendar/<int:year>/<int:month>", methods=['GET'])
def mood_calendar(year=None, month=None):
    if 'username' not in session:
        flash("Please log in to view the mood calendar.", 'warning')
        return redirect(url_for('auth.login'))
    
    username = session['username']

    if year is None or month is None:
        now = datetime.now()
        year = now.year
        month = now.month
    
    if not 1 <= month <= 12:
        flash("Invalid month specified.", 'error')
        return redirect(url_for('mood_calendar.mood_calendar'))
    
    monthly_mood_data = get_monthly_mood_data(username, year, month)

    processed_mood_data = {}
    for day, log in monthly_mood_data.items():
        day_entries = []
        for log in log:
            styling = get_emotion_styling(log['emotion'])
            day_entries.append({
                'emotion': log['emotion'],
                'note': log.get('note', ''),
                'timestamp': log.get('timestamp', ''),
                'color': styling['color'],
                'emoji': styling['emoji']
            })

        processed_mood_data[day] = {
            'total_entries': len(day_entries),
            'entries': day_entries,
        }

    month_name = datetime(year, month, 1).strftime("%B")    
    
    cal_data = calendar.monthcalendar(year, month)
    mood_summary = calculate_mood_summary(processed_mood_data)

    return render_template("mood_calendar.html",
                            year=year,
                            month_name=month_name,
                            calendar=cal_data,
                            mood_data=processed_mood_data,
                            mood_summary=mood_summary,
    )