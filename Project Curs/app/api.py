from flask import Blueprint, request, jsonify
from flask_restful import Api, Resource
from flask_login import login_required, current_user
from app.speech_recognition import recognize_speech
from app.punctuation import punctuate_text
from app.translation import translate_text

api_bp = Blueprint('api', __name__)
api = Api(api_bp)

class SpeechToText(Resource):
    def post(self):
        audio_file = request.files.get('audio')
        language_code = request.form.get('language', 'ru')
        if not audio_file:
            return {'error': 'No audio file provided'}, 400
        text = recognize_speech(audio_file, language_code=language_code)
        return {'text': text}

class Translate(Resource):
    def post(self):
        data = request.get_json()
        text = data.get('text')
        target_language = data.get('target_language')
        mode = data.get('mode', 'online')
        if not text or not target_language:
            return {'error': 'Missing text or target_language'}, 400
        translated = translate_text(text, target_language, mode)
        return {'translated': translated}

class History(Resource):
    @login_required
    def get(self):
        return jsonify([])

api.add_resource(SpeechToText, '/api/speech-to-text')
api.add_resource(Translate, '/api/translate')
api.add_resource(History, '/api/history') 