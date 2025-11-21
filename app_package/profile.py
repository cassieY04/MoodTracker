from flask import Blueprint, request, redirect, url_for, flash, session, render_template
from .users import UserManager
from .validation import password_requirement, validate_email, validate_phone

profile_bp = Blueprint('profile', __name__)

@profile_bp.route("/profile/<username>", methods=["GET", "POST"]) #add bunch of things
def profile(username):
    if not UserManager.user_exists(username):
        flash("User not found.")
        return redirect(url_for("home.homepage"))

    user = UserManager.get_user(username)

    if request.method == "POST":
        if 'delete' in request.form:
            confirm_delete = request.form.get("confirm_delete")
            if confirm_delete != "yes":
                flash("Account deletion cancelled.")
                return redirect(url_for("profile.profile", username=username))
            
            UserManager.delete_user(username)
            session.pop('username', None)
            flash("Your account has been successfully deleted.")
            return redirect(url_for("home.homepage"))
        
        confirm = request.form.get("confirm")
        if confirm != "yes":
            flash("Update cancelled.")
            return redirect(url_for("profile.profile", username=username))

        new_phone = request.form["phone"].strip()
        new_email = request.form["email"].strip()
        new_password = request.form["password"].strip()

        update_data = {}
        
        if new_phone:
            if not validate_phone(new_phone):
                flash("Phone number must contain only digits and have 8-12 characters.")
                return redirect(url_for("profile.profile", username=username))
            update_data["phone"] = new_phone
            
        if new_email:
            if not validate_email(new_email):
                flash("Email must end with @gmail.com address.")#remove
                return redirect(url_for("profile.profile", username=username))
            update_data["email"] = new_email
            
        if new_password:
            error = password_requirement(new_password)
            if error:
                flash(error)
                return redirect(url_for("profile.profile", username=username))
            update_data["password"] = new_password

        if update_data:
            UserManager.update_user(username, update_data)
            flash("Profile updated successfully!")
            
        return redirect(url_for("profile.profile", username=username))

    return render_template("profile.html", username=username, user=user)