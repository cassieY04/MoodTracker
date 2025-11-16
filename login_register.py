from flask import Blueprint, request, redirect, url_for, flash, session, render_template
from users import UserManager
from validation import password_requirement, validate_email, validate_phone

auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        phone = request.form["phone"].strip()
        email = request.form["email"].strip()
        password = request.form["password"].strip()

        if not username or not phone or not email or not password:
            flash("All fields are required.")
            return redirect(url_for("auth.register"))

        if UserManager.user_exists(username):
            flash("Username already exists.")
            return redirect(url_for("auth.register"))
        
        if not validate_email(email):
            flash("Email must be a @gmail.com address.")
            return redirect(url_for("auth.register"))

        if not validate_phone(phone):
            flash("Phone number must contain only digits and be 8-12 characters long.")
            return redirect(url_for("auth.register"))

        error = password_requirement(password)
        if error:
            flash(error)
            print(f"DEBUG: Password error: {error}")
            return redirect(url_for("auth.register"))
        
        print("DEBUG: All validations passed!")
        UserManager.add_user(username, {
            "phone": phone,
            "email": email,
            "password": password
        })
        flash("Registration successful!")
        return redirect(url_for("home.homepage"))

    return render_template("register.html")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if not UserManager.user_exists(username):
            flash("Username not found.")
            return redirect(url_for("auth.login"))

        user = UserManager.get_user(username)
        if user["password"] != password:
            flash("Incorrect password.")
            return redirect(url_for("auth.login"))

        session['username'] = username
        flash(f"You're in! Let's get started, {username}!")
        return redirect(url_for("home.dashboard"))

    return render_template("login.html")

@auth_bp.route("/logout")
def logout():
    session.pop('username', None)
    flash("You have been logged out.")
    return redirect(url_for("home.homepage"))