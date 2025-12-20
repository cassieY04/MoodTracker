from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from .users import UserManager
from .logemotion import get_emotion_styling

emotion_history_bp = Blueprint('emotion_history', __name__)

@emotion_history_bp.route("/emotionhistory")
def emotion_history():
    if 'username' not in session:
        flash("Please login to view your history.", "warning")
        return redirect(url_for('auth.login'))
        
    username = session['username']
    logs = UserManager.get_emotion_logs(username)

    if request.method == 'POST':
        action = request.form.get('action')
        log_id = request.form.get('log_id')

        if action == 'edit':
            new_note = request.form.get("note")
            if UserManager.update_emotion_log(log_id, username, new_note):
                flash("Entry updated successfully.", "success")
            else:
                flash("Error updating entry.", "error")

        return redirect(url_for('emotion_history.emotion_history', logs=logs))
    
    # Enhance logs with emoji and color for the UI
    for log in logs:
        style = get_emotion_styling(log['emotion_name'])
        log['emoji'] = style['emoji']
        log['color'] = style['color']
        
    return render_template("emotion_history.html", logs=logs)
