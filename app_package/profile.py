from flask import Blueprint, request, redirect, url_for, flash, session, render_template
from .users import UserManager
from .validation import password_requirement, validate_email, validate_phone
from datetime import datetime

profile_bp = Blueprint('profile', __name__)

@profile_bp.route("/profile/<username>", methods=["GET", "POST"]) 
def profile(username):
    if not UserManager.user_exists(username):
        flash("User not found.")
        return redirect(url_for("home.homepage"))

    user = UserManager.get_user(username)

    if request.method == "POST":
        if 'delete' in request.form:
            UserManager.delete_user(username)
            session.pop('username', None)
            flash("Your account has been successfully deleted.")
            return redirect(url_for("home.homepage"))
        
        update_data = {}
        new_username = request.form.get("username", "").strip()
        new_phone = request.form.get("phone", "").strip()
        new_email = request.form.get("email", "").strip()
        new_password = request.form.get("password", "").strip()
        new_bio = request.form.get("bio", "").strip()
        new_address = request.form.get("address", "").strip()
        new_birthday = request.form.get("birthday", "").strip()
        new_gender = request.form.get("gender", "").strip()
        new_profile_picture = request.form.get("profile_picture", "").strip()

        if new_username and new_username != user["username"]:
            existing_user = UserManager.get_user_by_username_or_email(new_username)
            if existing_user:
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
            
            existing_user = UserManager.get_user_by_username_or_email(new_email)
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

        if new_bio:
            update_data["bio"] = new_bio
        if new_address:
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
                update_data["birthday"] = new_birthday
                update_data["age"] = age
            except ValueError:
                flash("Invalid birthday format. Use DD-MM-YYYY.")
                return redirect(url_for("profile.profile", username=username))
        if new_profile_picture:
            update_data["profile_picture"] = new_profile_picture    

        if update_data:
            UserManager.update_user(username, update_data)
            flash("Profile updated successfully!")
            
        return redirect(url_for("profile.profile", username=username))

    return render_template("profile.html", username=username, user=user)