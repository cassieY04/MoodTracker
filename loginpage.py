#Santania Part

from flask import Flask, render_template, request, redirect, url_for, flash, session

app = Flask(__name__)
app.secret_key = "secret123"  

users = {}

def password_requirement(password): #KX display the short requirements
    if len(password) < 8 or len(password) > 12:
        return "Password must be between 8 and 12 characters long."
    if not any(c.isupper() for c in password):
        return "Password must contain at least one uppercase letter."
    if not any(c.islower() for c in password):
        return "Password must contain at least one lowercase letter."
    if not any(c.isdigit() for c in password):
        return "Password must contain at least one digit."
    if not any(c in "@_-*#" for c in password):
        return "Password must contain at least one special character (@, _, - ,* or #)."
    return None  

def validate_email(email):
    return email.endswith('@gmail.com')

def validate_phone(phone):
    return phone.isdigit() and 8 <= len(phone) <= 12

@app.route("/")
def homepage():
    return render_template("index.html") #KeXin will handle 


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        phone = request.form["phone"].strip()
        email = request.form["email"].strip()
        password = request.form["password"].strip()

        if not username or not phone or not email or not password:
            flash("All fields are required.")
            return redirect(url_for("register"))

        if username in users:
            flash("Username already exists.")
            return redirect(url_for("register"))
        
        if not validate_email(email):
            flash("Email must be a @gmail.com address.")
            return redirect(url_for("register"))

        if not validate_phone(phone):
            flash("Phone number must contain only digits and be 8-12 characters long.")
            return redirect(url_for("register"))

        error = password_requirement(password)
        if error:
            flash(error)
            return redirect(url_for("register"))

        users[username] = {
            "phone": phone,
            "email": email,
            "password": password
        }
        flash("Registration successful!")
        return redirect(url_for("homepage"))

    return render_template("register.html")#KeXin will handle 


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username not in users:
            flash("Username not found.")
            return redirect(url_for("login"))

        if users[username]["password"] != password:
            flash("Incorrect password.")
            return redirect(url_for("login"))

        session['username']=username
        flash(f"You're in!Let's get started, {username}!")
        return redirect(url_for("profile", username=username))

    return render_template("login.html")#KeXin will handle 

#Profile Update
@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    if username not in users:
        flash("User not found.")
        return redirect(url_for("homepage"))

    user = users[username]

    if request.method == "POST":

        if 'delete' in request.form:
            confirm_delete = request.form.get("confirm_delete")
            if confirm_delete != "yes":
                flash("Account deletion cancelled.")
                return redirect(url_for("profile", username=username))
            
            del users[username]
            session.pop('username', None)
            flash("Your account has been successfully deleted.")
            return redirect(url_for("homepage"))
        
        confirm = request.form.get("confirm")
        if confirm != "yes":
            flash("Update cancelled.")
            return redirect(url_for("profile", username=username))

        new_phone = request.form["phone"].strip()
        new_email = request.form["email"].strip()
        new_password = request.form["password"].strip()

        if new_phone:
            if not validate_phone(new_phone):
                flash("Phone number must contain only digits and be 8-12 characters long.")
                return redirect(url_for("profile", username=username))
            user["phone"] = new_phone
        if new_email:
            if not validate_email(new_email):
                flash("Email must be a @gmail.com address.")
                return redirect(url_for("profile", username=username))
            user["email"] = new_email
        if new_password:
            error = password_requirement(new_password)
            if error:
                flash(error)
                return redirect(url_for("profile", username=username))
            user["password"] = new_password

        flash("Profile updated successfully!")
        return redirect(url_for("profile", username=username))
    #KeXin will handle -html
    return render_template("profile.html", username=username, user=user)

@app.route("/logout")
def logout():
    session.pop('username', None)
    flash("You have been logged out.")
    return redirect(url_for("homepage"))


if __name__ == "__main__":
    app.run(debug=True)
