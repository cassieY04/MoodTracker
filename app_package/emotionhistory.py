from flask import Blueprint, render_template, session, redirect, url_for, flash
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
    
    # Enhance logs with emoji and color for the UI
    for log in logs:
        style = get_emotion_styling(log['emotion_name'])
        log['emoji'] = style['emoji']
        log['color'] = style['color']
        
    return render_template("emotion_history.html", logs=logs)
