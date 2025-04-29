# app/__init__.py
# Инициализация Flask-приложения и регистрация маршрутов (routes)

from flask import Flask

def create_app(template_folder=None, static_folder=None):
    app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)

    from app.routes import bp
    app.register_blueprint(bp)

    return app
