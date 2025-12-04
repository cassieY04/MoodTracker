from flask import Blueprint, render_template, session, redirect, url_for, flash

log_emotion_bp = Blueprint('log_emotion', __name__)

@log_emotion_bp.route("/log_emotion")
def log_emotion():
    return render_template("log_emotion.html")