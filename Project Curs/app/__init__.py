# app/__init__.py
# Инициализация Flask-приложения и регистрация маршрутов (routes)

from flask import Flask
from flask_login import LoginManager
# from .models import db, User  # Removed database-related imports
from .api import api_bp

def create_app(template_folder=None, static_folder=None):
    app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)

    from app.routes import bp
    app.register_blueprint(bp)
    app.register_blueprint(api_bp)

    # db.init_app(app)  # Removed database initialization

    login_manager = LoginManager()
    login_manager.login_view = 'routes.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return None  # Adjusted to return None since no database is used

    return app
