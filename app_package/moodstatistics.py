from flask import Blueprint, render_template, session, redirect, url_for, request
from .users import UserManager
from collections import Counter
from datetime import datetime, timedelta, timezone
import calendar
from .logemotion import get_emotion_styling

mood_statistics_bp = Blueprint('mood_statistics', __name__)

@mood_statistics_bp.route("/mood_statistics")
def mood_statistics():
    if 'username' not in session:
        return redirect(url_for('auth.login'))

    username = session['username']
    period = request.args.get('period', 'daily') # Default to daily
    date_param = request.args.get('date')
    month_param = request.args.get('month')
    week_param = request.args.get('week')

    # Fetch all logs
    all_logs = UserManager.get_emotion_logs(username)
    
    # Filter logs based on period
    filtered_logs = []
    
    # Use Malaysia Time (UTC+8) to match logemotion.py
    msia_tz = timezone(timedelta(hours=8))
    now = datetime.now(msia_tz).replace(tzinfo=None) # Make naive for string comparisons
    selected_date = now
    selected_month = now.strftime('%Y-%m')
    
    # Calculate current ISO week for default value
    isocal = now.isocalendar()
    selected_week = f"{isocal.year}-W{isocal.week:02d}"

    if date_param:
        try:
            selected_date = datetime.strptime(date_param, '%Y-%m-%d')
        except ValueError:
            pass # Fallback to now if invalid
    
    if period == 'daily':
        today_str = selected_date.strftime('%Y-%m-%d')
        filtered_logs = [l for l in all_logs if l['timestamp'].startswith(today_str)]
        
        if selected_date.date() == now.date():
            period_title = "Today"
        else:
            period_title = selected_date.strftime('%b %d, %Y')
            
    elif period == 'monthly':
        if month_param:
            selected_month = month_param
            
        month_str = selected_month
        filtered_logs = [l for l in all_logs if l['timestamp'].startswith(month_str)]
        
        # Title
        try:
            dt = datetime.strptime(month_str, '%Y-%m')
            if dt.strftime('%Y-%m') == now.strftime('%Y-%m'):
                period_title = "This Month"
            else:
                period_title = dt.strftime('%B %Y')
        except ValueError:
            period_title = "Selected Month"
            
    else: # weekly (default)
        if week_param:
            selected_week = week_param
            try:
                # Parse ISO week (YYYY-Www)
                y, w = map(int, week_param.split('-W'))
                week_start = datetime.fromisocalendar(y, w, 1)
                week_end = week_start + timedelta(days=7)
                
                filtered_logs = []
                for l in all_logs:
                    ts = l.get('timestamp')
                    if ts:
                        l_date = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
                        if week_start <= l_date < week_end:
                            filtered_logs.append(l)
                
                end_display = week_end - timedelta(days=1)
                period_title = f"{week_start.strftime('%b %d')} - {end_display.strftime('%b %d')}"
            except (ValueError, AttributeError):
                # Fallback if parsing fails
                week_start = now - timedelta(days=7)
                period_title = "Last 7 Days"
        else:
            # Default: Last 7 Days (Rolling)
            week_start = now - timedelta(days=7)
            filtered_logs = []
            for l in all_logs:
                try:
                    ts = l.get('timestamp')
                    if ts:
                        l_date = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
                        if l_date >= week_start:
                            filtered_logs.append(l)
                except ValueError:
                    continue
            period_title = "Last 7 Days"

    # --- 1. Calculate Summary Stats for Period ---
    total_logs = len(filtered_logs)
    
    if filtered_logs:
        emotions = [l['emotion_name'] for l in filtered_logs]
        top_mood = Counter(emotions).most_common(1)[0][0]
    else:
        top_mood = "-"

    # Streak is calculated on ALL logs to show current active streak
    streak = calculate_streak(all_logs)

    # --- 2. Breakdown for Colored Bars ---
    emotion_counts = Counter([l['emotion_name'] for l in filtered_logs])
    breakdown = []
    for emo, count in emotion_counts.items():
        percent = (count / total_logs) * 100 if total_logs > 0 else 0
        style = get_emotion_styling(emo)
        breakdown.append({
            'name': emo,
            'count': count,
            'percent': round(percent, 1),
            'color': style['color'],
            'emoji': style['emoji'],
            'icon': style.get('icon')
        })
    # Sort by count descending
    breakdown.sort(key=lambda x: x['count'], reverse=True)

    # --- 3. Prepare Data for Charts ---
    
    # A. Pie Chart Data
    pie_labels = [item['name'] for item in breakdown]
    pie_data = [item['count'] for item in breakdown]
    pie_colors = [item['color'] for item in breakdown]

    # B. Line Chart Data
    mood_scores = {
        'Happy': 3, 'Excited': 3,
        'Neutral': 2,
        'Sad': 1, 'Anxious': 1, 'Stressed': 1, 'Angry': 1
    }
    line_labels = []
    line_data = []

    if period == 'daily':
        # Chronological order for today
        sorted_logs = sorted(filtered_logs, key=lambda x: x['timestamp'])
        for log in sorted_logs:
            time_str = log['timestamp'].split(' ')[1][:5] # HH:MM
            line_labels.append(time_str)
            line_data.append(mood_scores.get(log.get('emotion_name'), 2))
            
    elif period == 'monthly':
        # Daily averages for the month
        dt_month = datetime.strptime(selected_month, '%Y-%m')
        num_days = calendar.monthrange(dt_month.year, dt_month.month)[1]
        days_data = {day: [] for day in range(1, num_days + 1)}
        
        for log in filtered_logs:
            ts = log.get('timestamp')
            if ts:
                day = int(ts.split(' ')[0].split('-')[2])
                score = mood_scores.get(log.get('emotion_name'), 2)
                days_data[day].append(score)
        
        for day in range(1, num_days + 1):
            # Only show up to today if it's the current month
            current_date = datetime(dt_month.year, dt_month.month, day)
            if current_date > now:
                break
                
            line_labels.append(str(day))
            scores = days_data[day]
            if scores:
                line_data.append(round(sum(scores)/len(scores), 1))
            else:
                line_data.append(None)

    else: # Weekly
        # Prepare chart labels
        chart_days = {}
        
        if week_param:
            # Specific week: Mon -> Sun
            for i in range(7):
                d = week_start + timedelta(days=i)
                chart_days[d.strftime('%Y-%m-%d')] = []
        else:
            # Rolling 7 days
            today_date = now.date()
            for i in range(6, -1, -1):
                d = today_date - timedelta(days=i)
                chart_days[d.strftime('%Y-%m-%d')] = []
            
        for log in filtered_logs:
             ts = log.get('timestamp')
             if ts:
                log_date = ts.split(' ')[0]
                if log_date in chart_days:
                    score = mood_scores.get(log.get('emotion_name'), 2)
                    chart_days[log_date].append(score)
        
        for date_str, scores in chart_days.items():
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            line_labels.append(dt.strftime('%a'))
            if scores:
                line_data.append(round(sum(scores)/len(scores), 1))
            else:
                line_data.append(None)

    return render_template(
        "mood_statistics.html",
        period=period,
        period_title=period_title,
        selected_date=selected_date.strftime('%Y-%m-%d'),
        selected_month=selected_month,
        selected_week=selected_week,
        total_logs=total_logs,
        top_mood=top_mood,
        streak=streak,
        breakdown=breakdown,
        pie_labels=pie_labels,
        pie_data=pie_data,
        pie_colors=pie_colors,
        line_labels=line_labels,
        line_data=line_data
    )

def calculate_streak(logs):
    """Calculates current consecutive days of logging."""
    if not logs:
        return 0
    
    # Get unique dates logged
    dates = set()
    for log in logs:
        ts = log.get('timestamp')
        if ts:
            dates.add(ts.split(' ')[0])
    
    # Use Malaysia Time for streak calculation too
    msia_tz = timezone(timedelta(hours=8))
    now_msia = datetime.now(msia_tz)
    today = now_msia.date().strftime('%Y-%m-%d')
    yesterday = (now_msia - timedelta(days=1)).date().strftime('%Y-%m-%d')
    
    # Check if streak is active (logged today or yesterday)
    if today in dates:
        current_check = today
    elif yesterday in dates:
        current_check = yesterday
    else:
        return 0 # Streak broken
    
    streak = 0
    while current_check in dates:
        streak += 1
        # Move to previous day
        dt = datetime.strptime(current_check, '%Y-%m-%d')
        current_check = (dt - timedelta(days=1)).strftime('%Y-%m-%d')
        
    return streak