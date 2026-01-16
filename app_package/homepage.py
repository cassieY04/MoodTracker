from flask import Blueprint, render_template, session, redirect, url_for, flash
from .users import UserManager

home_bp = Blueprint('home', __name__)

@home_bp.route("/")
def homepage():
    return render_template("index.html")

@home_bp.route("/dashboard")
def dashboard():
    if 'username' not in session:
        flash("Please login first.")
        return redirect(url_for("auth.login"))
    
    username = session.get('username')
    user = UserManager.get_user(username)
    
    # Safety check: If session exists but user is deleted from DB
    if not user:
        session.clear()
        return redirect(url_for("auth.login"))
        
    show_popup = session.pop("show_welcome_popup", False)
    return render_template("dashboard.html", username=username, show_popup=show_popup, user=user)