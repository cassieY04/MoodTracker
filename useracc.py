#Santania Part

from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = "secret123"  

users = {}

def password_requirement(password):
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


@app.route("/")
def homepage():
    return render_template("index.html")


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

    return render_template("register.html")


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

        flash(f"You're in!Let's get started, {username}!")
        return redirect(url_for("profile", username=username))

    return render_template("login.html")

#Profile Update
@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    if username not in users:
        flash("User not found.")
        return redirect(url_for("homepage"))

    user = users[username]

    if request.method == "POST":
        confirm = request.form.get("confirm")
        if confirm != "yes":
            flash("Update cancelled.")
            return redirect(url_for("profile", username=username))

        new_phone = request.form["phone"].strip()
        new_email = request.form["email"].strip()
        new_password = request.form["password"].strip()

        if new_phone:
            user["phone"] = new_phone
        if new_email:
            user["email"] = new_email
        if new_password:
            error = password_requirement(new_password)
            if error:
                flash(error)
                return redirect(url_for("profile", username=username))
            user["password"] = new_password

        flash("Profile updated successfully!")
        return redirect(url_for("profile", username=username))

    return render_template("profile.html", username=username, user=user)


if __name__ == "__main__":
    app.run(debug=True)
