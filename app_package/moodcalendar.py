from flask import Blueprint, render_template, session, redirect, url_for, flash

mood_calendar_bp = Blueprint('mood_calendar', __name__)

@mood_calendar_bp.route("/mood_calendar")
def mood_calendar():
    return render_template("mood_calendar.html")