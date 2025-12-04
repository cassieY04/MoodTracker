from flask import Blueprint, render_template, session, redirect, url_for, flash

mood_statistics_bp = Blueprint('mood_statistics', __name__)

@mood_statistics_bp.route("/mood_statistics")
def mood_statistics():
    
    return render_template("mood_statistics.html")
