from flask import Blueprint, render_template, session, redirect, url_for, flash

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
    show_popup = session.pop("show_welcome_popup", False)
    return render_template("dashboard.html", username=username, show_popup=show_popup)