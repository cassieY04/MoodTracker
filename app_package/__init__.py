from flask import Flask
from Databases.userdb import init_db

def create_app():
    app = Flask(__name__)
    app.secret_key = "secret123"

    app.config['DATABASE_FILE'] = 'user.db'
    
    from app_package.homepage import home_bp
    from app_package.login_register import auth_bp
    from app_package.profile import profile_bp

    with app.app_context():
        init_db()
    
    app.register_blueprint(home_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(profile_bp)
    
    return app
   