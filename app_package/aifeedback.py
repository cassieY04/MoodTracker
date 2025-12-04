from flask import Blueprint, render_template, session, redirect, url_for, flash

ai_feedback_bp = Blueprint('ai_feedback', __name__)

@ai_feedback_bp.route("/ai_feedback")
def ai_feedback():

    return render_template("ai_feedback.html")
