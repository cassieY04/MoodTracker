from flask import Blueprint, request, redirect, url_for, flash, session, render_template
from .users import UserManager
from .validation import password_requirement, validate_email, validate_phone, validate_security_question, validate_security_answer  

auth_bp = Blueprint('auth', __name__)

SECURITY_QUESTIONS = [
    "What is your favourite food?",
    "What was your dream car?",
    "What is your first phone brand?"
]


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        fullname = request.form["fullname"].strip()
        username = request.form["username"].strip()
        phone = request.form["phone"].strip()
        email = request.form["email"].strip()
        password = request.form["password"].strip()
        confirm = request.form["confirm_password"].strip()
        question = request.form["security_question"]
        answer = request.form["security_answer"].strip().lower()

        if not username or not phone or not email or not password or not confirm or not question or not answer:
            flash("All fields are required to fill.")
            return redirect(url_for("auth.register"))

        if UserManager.get_user_by_username(username):
            flash("Username already exists.")
            return redirect(url_for("auth.register"))
        if UserManager.get_user_by_email(email):
            flash("Email is already used by another account.")
            return redirect(url_for("auth.register"))
        
        question_error = validate_security_question(question, SECURITY_QUESTIONS)
        if question_error:
            flash(question_error)
            return redirect(url_for("auth.register"))

        answer_error = validate_security_answer(answer)
        if answer_error:
            flash(answer_error)
            return redirect(url_for("auth.register"))
        
        if not validate_email(email):
            flash("Email must end with @gmail.com address.")
            return redirect(url_for("auth.register"))

        if not validate_phone(phone):
            flash("Phone number must contain only digits and have 8-12 characters.")
            return redirect(url_for("auth.register"))
        
        if password != confirm:
            flash("Password and Confirm Password do not match.")
            return redirect(url_for("auth.register"))
        
        error = password_requirement(password)
        if error:
            flash(error)
            print(f"DEBUG: Password error: {error}")
            return redirect(url_for("auth.register"))
        
        print("DEBUG: All validations passed!")
        try:
            UserManager.add_user(username, {
                "fullname": fullname,
                "phone": phone,
                "email": email,
                "password": password,
                "security_question": question,
                "security_answer": answer
            })
        except ValueError as e:
            flash(str(e))
            return redirect(url_for("auth.register"))
        session["first_login_popup"] = True
        flash("Registration successful! Please log in.")
        return redirect(url_for("auth.login"))

    return render_template("register.html", security_questions=SECURITY_QUESTIONS)

@auth_bp.route("/login", methods=["GET", "POST"])#login
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
        if session.pop("first_login_popup", None):
            flash("🎉 Welcome! Thanks for registering MoodTracker!")

        return redirect(url_for("home.dashboard"))

    return render_template("login.html")

@auth_bp.route('/forgot', methods=['GET', 'POST'])
def forgot():
    if request.method == 'POST':
        identity = request.form.get("identity")  # username or email

        if not identity:
            flash("Please enter your username or email.")
            return redirect(url_for("auth.forgot"))

        user = UserManager.get_user_by_username_or_email(identity)

        if not user:
            flash("Username or email not found.")
            return redirect(url_for("auth.forgot"))

        #  store user temporarily for verification/reset
        session["reset_user"] = user["username"]

        flash("User verified. Please answer your security question.")
        return redirect(url_for("auth.verify_security"))

    return render_template("forgot.html")

@auth_bp.route('/verify', methods=['GET', 'POST'])
def verify_security():

    #  User must come from forgot page
    if "reset_user" not in session:
        flash("Session expired. Please try again.")
        return redirect(url_for("auth.forgot"))

    username = session["reset_user"]

    #  Get stored question & answer from DB
    user = UserManager.get_user(username)

    if not user:
        flash("User not found.")
        return redirect(url_for("auth.forgot"))

    real_question = user["security_question"]
    real_answer = user["security_answer"]   # already stored as lowercase

    # USER CLICKED VERIFY BUTTON
    if request.method == "POST":
        user_answer = request.form.get("security_answer")

        if not user_answer:
            flash("Please enter your answer.")
            return redirect(url_for("auth.verify_security"))

        # CASE-INSENSITIVE COMPARISON
        if user_answer.strip().lower() != real_answer.strip().lower():
            flash("Incorrect security answer.")
            return redirect(url_for("auth.verify_security"))

        # CORRECT ANSWER → MOVE TO RESET PAGE
        flash("Verification successful. Please reset your password.")
        return redirect(url_for("auth.reset_password"))

    return render_template("verify_security.html", question=real_question)


@auth_bp.route('/reset', methods=['GET', 'POST'])
def reset_password():
    if "reset_user" not in session:
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        new_password = request.form["new_password"]
        confirm = request.form["confirm_password"]

        if new_password != confirm:
            flash("Passwords do not match.")
            return redirect(url_for("auth.reset_password"))

        username = session["reset_user"]
        UserManager.update_user(username, {"password": new_password})

        session.pop("reset_user", None)
        flash("Password reset successful. Please log in.")
        return redirect(url_for("auth.login"))

    return render_template("reset.html")

@auth_bp.route("/logout", methods=["GET"])
def logout():
    session.pop('username', None)
    flash("You have been logged out.")
    return redirect(url_for("home.homepage"))

