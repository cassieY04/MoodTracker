from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from Databases.emologdb import get_db, save_emolog
from app_package.aifeedback import generate_short_feedback, generate_full_feedback
from datetime import datetime, timedelta, timezone

emotion_choice = ['Happy', 'Excited', 'Neutral', 'Anxious', 'Sad', 'Angry', 'Stressed']
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


log_emotion_bp = Blueprint('log_emotion', __name__)

@log_emotion_bp.route("/log_emotion", methods=['GET', 'POST'])
def emolog():

    if 'username' not in session:
            flash('You must be logged in to log an emotion.', 'warning')
            return redirect(url_for('auth.login'))
        
    username = session['username']
    ai_short = None
    show_feedback = False
    selected_emotion = None
    new_log_id = None
    
    if request.method == 'POST':
        selected_emotion = request.form.get('emotion')
        note = request.form.get('note', '').strip()
        thought = request.form.get('thought', '').strip()

        msia_tz = timezone(timedelta(hours=8))
        current_msia_time = datetime.now(msia_tz).strftime("%Y-%m-%d %H:%M:%S")
        
        ai_short = generate_short_feedback(selected_emotion, note, thought)
        ai_full = generate_full_feedback(selected_emotion, note, thought)

        new_log_id = save_emolog(
            username = session['username'],
            emotion = selected_emotion,
            note = note,
            thought = thought,
            ai_short = ai_short,
            ai_full = ai_full,
            timestamp = current_msia_time
        )

        if new_log_id:
            show_feedback = True
            flash("Emotion log saved successfully!", "success")
            flash(ai_short, "ai")
          
    return render_template("log_emotion.html", emotions=emotion_choice, aifeedback=ai_short, show_feedback=show_feedback, new_log_id=new_log_id)