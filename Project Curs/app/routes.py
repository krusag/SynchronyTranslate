# app/routes.py
# Основные маршруты веб-приложения

from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.speech_recognition import recognize_speech
from app.punctuation import punctuate_text
from app.translation import translate_text
from app.accent_config import get_available_languages
# from app.celery_worker import celery  # Temporarily commented out to avoid circular import
import uuid
import os
import signal
import sys

# Создаём blueprint для маршрутов
bp = Blueprint('routes', __name__)


@bp.route('/')
def index():
    """Отображение главной страницы"""
    languages = get_available_languages()
    return render_template("index.html", languages=languages)


@bp.route('/translate', methods=['POST'])
def translate():
    """Обработка аудиофайла и перевод текста"""
    try:
        # Получаем файл и параметры из запроса
        audio_file = request.files['audio']
        source_language = request.form.get('source_language', 'auto')  # язык распознавания (теперь по умолчанию auto)
        target_language = request.form.get('target_language', 'en')  # язык перевода
        mode = request.form.get('mode', 'online')  # по умолчанию онлайн-перевод

        # Распознавание речи с учетом выбранного языка и языка перевода
        recognized_text = recognize_speech(
            audio_file, 
            language_code=source_language,
            target_language=target_language
        )
        
        # Определяем, какой язык был использован (если был auto)
        actual_source_language = source_language
        if source_language == 'auto':
            # Если не можем определить, предполагаем русский
            # В продакшене здесь мог бы быть алгоритм определения языка по тексту
            for lang in ['ru', 'en', 'de', 'fr']:
                if recognized_text and any(c in recognized_text.lower() for c in get_language_specific_chars(lang)):
                    actual_source_language = lang
                    break
            if actual_source_language == 'auto':
                actual_source_language = 'ru'

        # Добавление пунктуации с учетом языка
        punctuated_text = punctuate_text(recognized_text, language_code=actual_source_language)

        # Перевод текста
        translated_text = translate_text(punctuated_text, target_language, mode)

        return jsonify({
            "original": punctuated_text,
            "translated": translated_text,
            "source_language": actual_source_language,
            "target_language": target_language
        })
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error: {error_details}")
        return jsonify({"error": f"Processing error: {str(e)}"}), 500

def get_language_specific_chars(lang):
    """Возвращает характерные символы для определения языка"""
    lang_chars = {
        'ru': 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя',
        'en': 'abcdefghijklmnopqrstuvwxyz',
        'de': 'äöüß',
        'fr': 'àâçéèêëîïôùûüÿœæ'
    }
    return lang_chars.get(lang, '')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        flash('Регистрация успешна! Войдите в систему.')
        return redirect(url_for('routes.login'))
    return render_template('register.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Вход выполнен успешно!')
            return redirect(url_for('routes.index'))
        else:
            flash('Неверный логин или пароль')
    return render_template('login.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы.')
    return redirect(url_for('routes.index'))

@bp.route('/history')
@login_required
def history():
    return render_template('history.html', history=[])

@bp.route('/translate_async', methods=['POST'])
def translate_async():
    from app.tasks import async_translate  # Move import here to avoid circular import
    audio_file = request.files['audio']
    source_language = request.form.get('source_language', 'ru')
    target_language = request.form.get('target_language', 'en')
    mode = request.form.get('mode', 'online')
    user_id = current_user.id if current_user.is_authenticated else None

    # Сохраняем временный файл
    temp_filename = f"temp_{uuid.uuid4().hex}.wav"
    temp_path = os.path.join('/tmp', temp_filename)
    audio_file.save(temp_path)

    # Запускаем задачу
    task = async_translate.delay(temp_path, source_language, target_language, mode, user_id)

    return jsonify({'task_id': task.id}), 202

@bp.route('/task_status/<task_id>')
def task_status(task_id):
    task = celery.AsyncResult(task_id)
    if task.state == 'PENDING':
        response = {'state': task.state}
    elif task.state == 'SUCCESS':
        response = {'state': task.state, 'result': task.result}
    else:
        response = {'state': task.state, 'info': str(task.info)}
    return jsonify(response)

@bp.route('/shutdown', methods=['POST'])
def shutdown():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()
    return 'Server shutting down...'
