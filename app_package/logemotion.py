from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from Databases.emologdb import get_db, save_emolog
from app_package.aifeedback import generate_short_feedback, generate_full_feedback



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
    
    if request.method == 'POST':
        selected_emotion = request.form.get('emotion')
        note = request.form.get('note', '').strip()
        thought = request.form.get('thought', '').strip()
        
        ai_short = generate_short_feedback(selected_emotion, note, thought)
        ai_full = generate_full_feedback(selected_emotion, note, thought)

        if save_emolog(
            username = session['username'],
            emotion = selected_emotion,
            note = note,
            thought = thought,
            ai_short = ai_short,
            ai_full = ai_full
        ):
            show_feedback = True
            flash(ai_short, "ai")
            flash("Emotion log saved successfully!", "success")
          
    return render_template("log_emotion.html", emotions=emotion_choice, aifeedback=ai_short, show_feedback=show_feedback)