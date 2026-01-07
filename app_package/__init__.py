from flask import Flask, request, session, jsonify
from Databases.userdb import init_db
from Databases.emologdb import init_emologdb
import os 

def create_app():
    
    BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    
    app = Flask(
        __name__,
        static_folder=os.path.join(BASE_DIR, 'static')
    )
    
    app.secret_key = "secret123"
    app.config['DATABASE_FILE'] = 'user.db'

    app.config['MAX_LOGIN_ATTEMPTS'] = 3
    app.config['LOCK_SECONDS'] = 10
    
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
        init_emologdb()
    
    app.register_blueprint(home_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(ai_feedback_bp)
    app.register_blueprint(log_emotion_bp)
    app.register_blueprint(mood_calendar_bp)
    app.register_blueprint(mood_statistics_bp)
    app.register_blueprint(emotion_history_bp)

    @app.route('/update_theme', methods=['POST'])
    def update_theme():
        data = request.get_json()
        if data and 'theme' in data:
            session['theme'] = data['theme']
            return jsonify({"success": True}), 200
        return jsonify({"success": False}), 400
    
    return app