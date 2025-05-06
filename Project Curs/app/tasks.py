from .celery_worker import celery
from app.speech_recognition import recognize_speech
from app.punctuation import punctuate_text
from app.translation import translate_text

@celery.task
def async_translate(audio_path, source_language, target_language, mode, user_id=None):
    # Здесь audio_path — путь к сохранённому аудиофайлу
    with open(audio_path, 'rb') as f:
        recognized_text = recognize_speech(f, language_code=source_language)
    punctuated_text = punctuate_text(recognized_text, language_code=source_language)
    translated_text = translate_text(punctuated_text, target_language, mode)
    return {
        'original': punctuated_text,
        'translated': translated_text
    } 