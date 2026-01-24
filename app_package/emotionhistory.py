from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from .users import UserManager
from .logemotion import get_emotion_styling
from datetime import datetime, timedelta, timezone

emotion_history_bp = Blueprint('emotion_history', __name__)

@emotion_history_bp.route("/emotionhistory", methods=["GET", "POST"])
def emotion_history():
    if 'username' not in session:
        flash("Please login to view your history.", "warning")
        return redirect(url_for('auth.login'))
        
    username = session['username']
    logs = UserManager.get_emotion_logs(username)
    
    # --- Filtering Logic ---
    filter_date = request.args.get('date')
    filter_emotion = request.args.get('emotion')

    if filter_date:
        # Filter by date (timestamp starts with YYYY-MM-DD)
        logs = [l for l in logs if l['timestamp'].startswith(filter_date)]
    
    if filter_emotion:
        logs = [l for l in logs if l['emotion_name'] == filter_emotion]

    if request.method == 'POST':
        action = request.form.get('action')
        log_id = request.form.get('log_id')

        if action == 'edit':
            new_emotion = request.form.get('emotion_name')
            new_note = request.form.get('note')
            new_thought = request.form.get('thought')

            # Find original log to preserve timestamp (don't move history to "now")
            current_log = next((log for log in logs if str(log['id']) == str(log_id)), None)
            # Use original timestamp if found, otherwise fallback to now
            updated_timestamp = current_log['timestamp'] if current_log else datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")

            if UserManager.update_emotion_log(log_id, username, new_emotion, new_note, new_thought, updated_timestamp):
                flash("Entry updated successfully.", "success")
            else:
                flash("Error updating entry.", "error")

        elif action == 'delete':
            if UserManager.delete_emotion_log(log_id, username):
                flash("Entry deleted successfully.", "success")
            else:
                flash("Error deleting entry.", "error")

        return redirect(url_for('emotion_history.emotion_history'))
    
    # Enhance logs with emoji and color for the UI
    for log in logs:
        style = get_emotion_styling(log['emotion_name'])
        log['emoji'] = style['emoji']
        log['color'] = style['color']
        log['icon'] = style.get('icon')
        
    return render_template("emotion_history.html", logs=logs)
