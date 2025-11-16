from flask import Flask

def create_app():
    app = Flask(__name__)
    app.secret_key = "secret123"
    
    from homepage import home_bp
    from login_register import auth_bp
    from profile import profile_bp
    
    app.register_blueprint(home_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(profile_bp)
    
    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)