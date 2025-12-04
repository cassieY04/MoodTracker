from flask import Flask
from Databases.userdb import init_db

def create_app():
    app = Flask(__name__)
    app.secret_key = "secret123"

    app.config['DATABASE_FILE'] = 'user.db'
    
    from app_package.homepage import home_bp
    from app_package.login_register import auth_bp
    from app_package.profile import profile_bp
    from app_package.aifeedback import ai_feedback_bp
    from app_package.logemotion import log_emotion_bp
    from app_package.moodcalendar import mood_calendar_bp
    from app_package.moodstatistics import mood_statistics_bp
    from app_package.emotionhistory import emotion_history_bp

    with app.app_context():
        init_db()
    
    app.register_blueprint(home_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(ai_feedback_bp)
    app.register_blueprint(log_emotion_bp)
    app.register_blueprint(mood_calendar_bp)
    app.register_blueprint(mood_statistics_bp)
    app.register_blueprint(emotion_history_bp)
    
    return app
   
app = create_app()

if __name__ == "__main__":
    app.run(debug=True)