# app/translation.py
# Локальный и онлайн перевод текста. Автоматическая загрузка argos-моделей

import os
import requests
from argostranslate import package, translate
from googletrans import Translator
import logging

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)

translator = Translator()

MODEL_DIR = "./models"
MODEL_URLS = {
    ("ru", "en"): "https://www.argosopentech.com/argospm/translate-ru_en.argosmodel",
    ("en", "ru"): "https://www.argosopentech.com/argospm/translate-en_ru.argosmodel",
    # Можно добавить другие пары, если появятся
}

def ensure_model_installed(from_code, to_code):
    """
    Проверяет, установлена ли модель перевода. Если нет — скачивает и устанавливает.
    """
    installed_languages = translate.get_installed_languages()
    from_lang = next((l for l in installed_languages if l.code == from_code), None)
    to_lang = next((l for l in installed_languages if l.code == to_code), None)

    if from_lang and to_lang:
        return  # Уже установлена

    os.makedirs(MODEL_DIR, exist_ok=True)
    url = MODEL_URLS.get((from_code, to_code))

    if not url:
        raise Exception(f"Локальная модель для {from_code} → {to_code} не поддерживается.")

    filename = os.path.join(MODEL_DIR, f"{from_code}_{to_code}.argosmodel")

    if not os.path.exists(filename):
        print(f"⏬ Скачиваем модель {from_code} → {to_code}...")
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception(f"Не удалось скачать модель: {response.status_code}")
        with open(filename, "wb") as f:
            f.write(response.content)

    # Проверка: является ли файл .zip (argosmodel = zip)
    if not zipfile_is_valid(filename):
        raise Exception("Файл модели повреждён или не является zip-архивом.")

    print("✅ Устанавливаем модель...")
    package.install_from_path(filename)
    print("✅ Модель установлена.")

def zipfile_is_valid(path):
    import zipfile
    try:
        with zipfile.ZipFile(path, 'r') as z:
            return z.testzip() is None
    except zipfile.BadZipFile:
        return False

def get_supported_offline_pairs():
    """
    Возвращает список поддерживаемых оффлайн-пар для перевода.
    """
    return list(MODEL_URLS.keys())

def translate_text(text, target_language, mode='online'):
    logging.debug(f"Translating text: {text} to {target_language} using mode: {mode}")
    try:
        if mode == 'local':
            source_lang = 'ru'  # Пока предполагаем только с русского
            if (source_lang, target_language) not in MODEL_URLS:
                warning = f"[Внимание] Оффлайн-перевод для пары {source_lang} → {target_language} не поддерживается. Используется онлайн-перевод."
                logging.warning(warning)
                result = translator.translate(text, dest=target_language)
                return f"{warning}\n{result.text}"
            ensure_model_installed(source_lang, target_language)

            installed_languages = translate.get_installed_languages()
            from_lang = next((l for l in installed_languages if l.code == source_lang), None)
            to_lang = next((l for l in installed_languages if l.code == target_language), None)

            if from_lang and to_lang:
                translation = from_lang.get_translation(to_lang)
                return translation.translate(text)
            else:
                return "Ошибка: локальная модель не установлена."
        else:
            result = translator.translate(text, dest=target_language)
            logging.debug(f"Translation result: {result.text}")
            return result.text
    except Exception as e:
        logging.error(f"Translation error: {str(e)}")
        return f"Ошибка перевода: {str(e)}"
