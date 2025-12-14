from flask import Blueprint, render_template, session, redirect, url_for, flash

emotion_history_bp = Blueprint('emotion_history', __name__)

@emotion_history_bp.route("/emotionhistory")
def emotion_history():
    
    return render_template("emotion_history.html")

