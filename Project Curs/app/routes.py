# app/routes.py
# Основные маршруты веб-приложения

from flask import Blueprint, request, jsonify, render_template
from app.speech_recognition import recognize_speech
from app.punctuation import punctuate_text
from app.translation import translate_text

# Создаём blueprint для маршрутов
bp = Blueprint('routes', __name__)


@bp.route('/')
def index():
    """Отображение главной страницы"""
    return render_template("index.html")


@bp.route('/translate', methods=['POST'])
def translate():
    """Обработка аудиофайла и перевод текста"""
    try:
        # Получаем файл и параметры из запроса
        audio_file = request.files['audio']
        target_language = request.form.get('target_language')
        mode = request.form.get('mode', 'online')  # по умолчанию онлайн-перевод

        # Распознавание речи
        recognized_text = recognize_speech(audio_file)

        # Добавление пунктуации
        punctuated_text = punctuate_text(recognized_text)

        # Перевод текста
        translated_text = translate_text(punctuated_text, target_language, mode)

        # Возвращаем результат
        return jsonify({
            "original": punctuated_text,
            "translated": translated_text,
            "language": target_language
        })
    except Exception as e:
        return jsonify({"error": f"Processing error: {str(e)}"}), 500
