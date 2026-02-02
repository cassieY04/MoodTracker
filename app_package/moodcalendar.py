from flask import Blueprint, render_template, session, redirect, url_for
import sqlite3
from datetime import datetime
import calendar
from Databases.emologdb import get_db
from .logemotion import EMOTION_MAP # Assumed to contain emotion dictionary

mood_calendar_bp = Blueprint('mood_calendar', __name__)

# 1. Define how your emotions map to the three main categories
EMOTION_CATEGORIES = {
    'Happy': 'Positive', 
    'Excited': 'Positive', 
    'Anxious': 'Negative', 
    'Sad': 'Negative', 
    'Angry': 'Negative', 
    'Stressed': 'Negative',
    'Neutral': 'Neutral', 
}

# 2. Define the final output titles and emojis (4 Outcomes + N/A)
EMOTIONAL_PATTERN_RESULT = {
    'Mostly Positive': {'title': 'Mostly Positive', 'emoji': '😊', 'icon': 'positive.png'},
    'Stress-Dominant': {'title': 'Stress-Dominant', 'emoji': '😔', 'icon': 'negative.png'},
    'Mixed Emotion': {'title': 'Mixed Emotion', 'emoji': '🔀', 'icon': 'mixedemo.png'}, 
    'Emotionally Balanced': {'title': 'Emotionally Balanced', 'emoji': '⚖️', 'icon': 'balanced.png'},
    'N/A': {'title': 'No Entries', 'emoji': '✍', 'icon': 'entry.png'},
}

# 3. Calculation function (implements the rules for emotional pattern)
def calculate_emotional_pattern(emotion_counts, total_entries):
    """
    Calculates the Emotional Pattern based on the decision rules for 4 outcomes,
    prioritizing dominance checks before falling back to balanced/mixed.
    """
    if total_entries == 0:
        return EMOTIONAL_PATTERN_RESULT['N/A']
    
    category_counts = {
        'Positive': 0,
        'Negative': 0,
        'Neutral': 0
    }
    
    # Group counts into categories
    for item in emotion_counts:
        emotion_name = item['emotion']
        count = item['count']
        
        # Look up the category; default to 'Neutral' if missing (safeguard)
        category = EMOTION_CATEGORIES.get(emotion_name, 'Neutral') 
        category_counts[category] += count

    # Calculate Percentages
    positive_pct = category_counts['Positive'] / total_entries
    negative_pct = category_counts['Negative'] / total_entries
    neutral_pct = category_counts['Neutral'] / total_entries 
    
    # Get the highest count for comparison later
    max_count = max(category_counts['Positive'], category_counts['Negative'], category_counts['Neutral'])
    
    # --- Apply Decision Rules (New Order) ---
    # Rule 1: Mostly Positive (Positive > 50%)
    if positive_pct > 0.5:
        return EMOTIONAL_PATTERN_RESULT['Mostly Positive']
        
    # Rule 2: Stress-Dominant (Negative/Stress > 50%)
    if negative_pct > 0.5:
        return EMOTIONAL_PATTERN_RESULT['Stress-Dominant']
    
    # Rule 3: Emotionally Balanced (Neutral is the largest category)
    # This rule triggers if Neutral is the single most frequent category.
    # This handles the case where Neutral is high (e.g., 40%) but not dominant (>50%) 
    # and should be categorized as 'Emotionally Balanced'.
    if neutral_pct == max_count / total_entries:
        return EMOTIONAL_PATTERN_RESULT['Emotionally Balanced']
    
    # Rule 4: Mixed Emotion (Fallback)
    # This is the final fallback, triggered only when no single category dominates AND 
    # Neutral is NOT the largest category. This implies true balance.
    return EMOTIONAL_PATTERN_RESULT['Mixed Emotion'] 


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
                strftime('%H:%M', timestamp) as time_str,
                emotion_name, 
                note,
                thought,
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
            emotion = row['emotion_name']
            style = EMOTION_MAP.get(emotion, {'color': '#CCCCCC', 'emoji': '🤷', 'icon': 'default.png'})
            
            entry = {
                'emotion': emotion,
                'note': row['note'],
                'thought': row['thought'],
                'timestamp': row['timestamp'],
                'time': row['time_str'],
                'emoji': style['emoji'],
                'icon': style.get('icon')
            }
            
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
    # Logic is reused, provides raw counts needed for the pattern calculation
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
            style = EMOTION_MAP.get(emotion, {'color': '#CCCCCC', 'emoji': '🤷', 'icon': 'default.png'})
            counts.append({
                'emotion': emotion,
                'count': row['count'],
                'emoji': style['emoji'],
                'color': style['color'],
                'icon': style.get('icon')
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
        
    mood_data = get_monthly_mood_data(username, year, month)
    emotion_counts = get_monthly_emotion_counts(username, year, month)
    
    # --- SUMMARY CALCULATION ---
    total_entries = sum(item['count'] for item in emotion_counts)
    
    # Calculate the Emotional Pattern using the new logic
    emotional_pattern = calculate_emotional_pattern(emotion_counts, total_entries)
    
    mood_summary = {
        'total_entries': total_entries,
        'emotional_pattern': emotional_pattern 
    }
    # ---------------------------
    
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