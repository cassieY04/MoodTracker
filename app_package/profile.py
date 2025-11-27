from flask import Blueprint, request, redirect, url_for, flash, session, render_template
from .users import UserManager
from .validation import password_requirement, validate_email,validate_phone, validate_security_question, validate_security_answer 
from datetime import datetime
from werkzeug.utils import secure_filename
import os
import uuid

profile_bp = Blueprint('profile', __name__)

SECURITY_QUESTIONS = [
    "What is your favourite food?",
    "What was your dream car?",
    "What is your first phone brand?"
]

UPLOAD_FOLDER = 'static/uploads/profile_pics'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_FILE_SIZE_MB = 5  

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def file_size_allowed(file):
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    return size <= MAX_FILE_SIZE_MB * 1024 * 1024

@profile_bp.route("/profile/<username>", methods=["GET", "POST"]) 
def profile(username):
    if not UserManager.user_exists(username):
        flash("User not found.")
        return redirect(url_for("home.homepage"))

    user = UserManager.get_user(username)
    update_data = {}

    if request.method == "POST":
       
        if 'delete' in request.form:
            UserManager.delete_user(username)
            session.pop('username', None)
            flash("Your account has been successfully deleted.")
            return redirect(url_for("home.homepage"))
            
        if 'delete_profile_picture' in request.form: #delete profile pic
            if user.get("profile_picture"):
                filepath = user["profile_picture"].replace("/static/", "static/")
                if os.path.exists(filepath):
                    os.remove(filepath)

            UserManager.update_user(username, {"profile_picture": None})
            flash("Profile picture deleted successfully.")
            return redirect(url_for("profile.profile", username=username))
            
        
        new_username = request.form.get("username", "").strip()
        new_phone = request.form.get("phone", "").strip()
        new_email = request.form.get("email", "").strip()
        new_password = request.form.get("password", "").strip()
        new_bio = request.form.get("bio", "").strip()
        new_address = request.form.get("address", "").strip()
        new_birthday = request.form.get("birthday", "").strip()
        new_gender = request.form.get("gender", "").strip()
        new_question = request.form.get("security_question", "").strip()
        new_answer = request.form.get("security_answer", "").strip().lower()

        if new_username and new_username != user["username"]:
            if UserManager.get_user_by_username(new_username):
                flash("Username is already taken.") 
                return redirect(url_for("profile.profile", username=username))
            update_data["username"] = new_username

        if new_phone:
            if not validate_phone(new_phone):
                flash("Phone number must contain only digits and have 8-12 characters.")
                return redirect(url_for("profile.profile", username=username))
            update_data["phone"] = new_phone
            
        
        if new_email and new_email != user["email"]:
            if not validate_email(new_email):
                flash("Email must end with @gmail.com address.")
                return redirect(url_for("profile.profile", username=username))
            existing_user = UserManager.get_user_by_email(new_email)
            if existing_user and existing_user["username"] != username:
                flash("Email is already used by another account.")
                return redirect(url_for("profile.profile", username=username))
            update_data["email"] = new_email
            
        
        if new_password:
            error = password_requirement(new_password)
            if error:
                flash(error)
                return redirect(url_for("profile.profile", username=username))
            update_data["password"] = new_password

        
        if new_bio is not None:
            update_data["bio"] = new_bio
        
        if new_address is not None:
            update_data["address"] = new_address
        
        if new_gender:
            if new_gender not in ["Male", "Female", "Others/Prefer not to say"]:
                flash("Invalid gender selection.")
                return redirect(url_for("profile.profile", username=username))
            update_data["gender"] = new_gender
        
        if new_birthday:
            try:
                birthday_date = datetime.strptime(new_birthday, "%d-%m-%Y").date()
                today = datetime.today().date()
                age = today.year - birthday_date.year - ((today.month, today.day) < (birthday_date.month, birthday_date.day))
                
                if not (7 <= age <= 100):
                    flash("Age must be between 7 and 100 years.")
                    return redirect(url_for("profile.profile", username=username))
                
                update_data["birthday"] = new_birthday
                update_data["age"] = age
            except ValueError:
                flash("Invalid birthday format. Use DD-MM-YYYY.")
                return redirect(url_for("profile.profile", username=username))
        
        #Profile picture upload
        file = request.files.get("profile_picture")
        if file and file.filename:
            if not allowed_file(file.filename):
                flash("Invalid file type for profile picture. Allowed: png, jpg, jpeg, gif.")
                return redirect(url_for("profile.profile", username=username))
            if not file_size_allowed(file):
                flash(f"File is too large. Maximum size is {MAX_FILE_SIZE_MB} MB.")
                return redirect(url_for("profile.profile", username=username))
            #Appends the username + timestamp in seconds to avoid overwriting.
            ext = secure_filename(file.filename).rsplit('.', 1)[1].lower()
            filename = f"{username}_{uuid.uuid4().hex}.{ext}"
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
            # store relative path for HTML
            update_data["profile_picture"] = url_for('static', filename=f'uploads/profile_pics/{filename}') 


        question_error = validate_security_question(new_question, SECURITY_QUESTIONS)
        if question_error:
            flash(question_error)
            return redirect(url_for("profile.profile", username=username))

        answer_error = validate_security_answer(new_answer)
        if answer_error:
            flash(answer_error)
            return redirect(url_for("profile.profile", username=username))
       
        update_data["security_question"] = new_question
        update_data["security_answer"] = new_answer

        if update_data:
            UserManager.update_user(username, update_data)
            flash("Profile updated successfully!")
        
        if "username" in update_data:
            session['username'] = update_data['username']
            username = update_data['username'] 
            
        return redirect(url_for("profile.profile", username=username))

    user = UserManager.get_user(username)

    return render_template(
        "profile.html", 
        username=username, 
        user=user,
        security_questions=SECURITY_QUESTIONS
    )