# app/accent_config.py
# Конфигурация акцентов для разных языков

ACCENT_CONFIGS = {
    'ru': {
        'model_id': "jonatasgrosman/wav2vec2-large-xlsr-53-russian",
        'description': 'Русский акцент',
        'sample_rate': 16000
    },
    'en': {
        'model_id': "facebook/wav2vec2-base-960h",
        'description': 'Английский акцент',
        'sample_rate': 16000
    },
    'de': {
        'model_id': "maxidl/wav2vec2-large-xlsr-german",
        'description': 'Немецкий акцент',
        'sample_rate': 16000
    },
    'fr': {
        'model_id': "facebook/wav2vec2-large-xlsr-53-french",
        'description': 'Французский акцент',
        'sample_rate': 16000
    }
}

def get_accent_config(language_code):
    """
    Возвращает конфигурацию акцента для указанного языка.
    Если язык не поддерживается, возвращает конфигурацию по умолчанию (русский).
    """
    return ACCENT_CONFIGS.get(language_code, ACCENT_CONFIGS['ru'])

def get_available_languages():
    """
    Возвращает список доступных языков с их описаниями.
    """
    return {code: config['description'] for code, config in ACCENT_CONFIGS.items()} 