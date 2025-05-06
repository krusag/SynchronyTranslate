# app/speech_recognition.py

import os
import torch
import librosa
import re
import numpy as np
from transformers import Wav2Vec2Processor, Wav2Vec2ForCTC
from app.utils import convert_audio
from app.accent_config import get_accent_config, ACCENT_CONFIGS
from app.audio_processing import preprocess_audio

MODEL_CACHE_DIR = "./models/wav2vec"

# Кэш для хранения загруженных моделей
loaded_models = {}

def download_model_if_needed(model_id):
    """
    Скачивает модель, если она еще не загружена.
    """
    if not os.path.exists(MODEL_CACHE_DIR):
        os.makedirs(MODEL_CACHE_DIR, exist_ok=True)
    
    local_model_dir = os.path.join(
        MODEL_CACHE_DIR, model_id.replace("/", os.sep)
    )
    
    if not os.path.exists(local_model_dir):
        print(f"⏬ Скачиваем wav2vec2 модель для {model_id}...")
        Wav2Vec2Processor.from_pretrained(model_id, cache_dir=MODEL_CACHE_DIR)
        Wav2Vec2ForCTC.from_pretrained(model_id, cache_dir=MODEL_CACHE_DIR)
        print("✅ Модель загружена.")
    else:
        print(f"✅ wav2vec2 модель {model_id} найдена локально.")

def get_model_for_language(language_code):
    """
    Возвращает модель и процессор для указанного языка.
    Если модель еще не загружена, загружает её.
    """
    if language_code not in loaded_models:
        config = get_accent_config(language_code)
        model_id = config['model_id']
        
        download_model_if_needed(model_id)
        
        processor = Wav2Vec2Processor.from_pretrained(model_id, cache_dir=MODEL_CACHE_DIR)
        model = Wav2Vec2ForCTC.from_pretrained(model_id, cache_dir=MODEL_CACHE_DIR)
        model.eval()
        
        loaded_models[language_code] = {
            'processor': processor,
            'model': model,
            'sample_rate': config['sample_rate']
        }
    
    return loaded_models[language_code]

def postprocess_text(text, language_code):
    """
    Минимальная постобработка распознанного текста.
    Для русского языка: замена ё на е, удаление двойных пробелов, первая буква заглавная.
    """
    if not text or len(text) <= 2:
        return text

    # Удаление лишних пробелов
    text = re.sub(r'\s+', ' ', text).strip()

    if language_code == 'ru':
        text = text.replace('ё', 'е').replace('Ё', 'Е')
        # Удаление двойных пробелов (на всякий случай)
        text = re.sub(r'\s+', ' ', text)
        # Базовая пунктуация: если нет точки, добавить в конец
        if text and text[-1] not in '.!?':
            text += '.'

    # Капитализация первой буквы
    if text and len(text) > 0 and text[0].isalpha():
        text = text[0].upper() + text[1:]

    return text

def detect_language(audio_file):
    """
    Пытается определить язык аудио, проверяя распознавание на разных языках
    и возвращая наиболее вероятный.
    """
    # Временный путь для конвертированного файла
    temp_path = convert_audio(audio_file)
    
    try:
        # Предобработка аудио только один раз
        enhanced_path = preprocess_audio(temp_path)
        
        languages = ['ru', 'en', 'de', 'fr']
        confidence_scores = {}
        
        for lang in languages:
            model_data = get_model_for_language(lang)
            processor = model_data['processor']
            model = model_data['model']
            sample_rate = model_data['sample_rate']
            
            # Загрузка и обработка аудио
            waveform, sr = librosa.load(enhanced_path, sr=sample_rate, mono=True)
            waveform = librosa.util.normalize(waveform)
            
            # Распознавание
            inputs = processor(waveform, sampling_rate=sample_rate, return_tensors="pt", padding=True)
            with torch.no_grad():
                outputs = model(**inputs)
            
            # Расчет уверенности модели
            logits = outputs.logits
            probs = torch.nn.functional.softmax(logits, dim=-1)
            confidence = torch.mean(torch.max(probs, dim=-1).values).item()
            confidence_scores[lang] = confidence
            
        # Определяем язык с наивысшей уверенностью
        most_confident_lang = max(confidence_scores, key=confidence_scores.get)
        return most_confident_lang, enhanced_path
        
    except Exception as e:
        print(f"Ошибка при определении языка: {str(e)}")
        return 'ru', temp_path  # Возвращаем русский по умолчанию в случае ошибки

def recognize_speech(audio_file, language_code='auto', target_language=None):
    """
    Распознаёт речь из аудиофайла и возвращает текст.
    :param audio_file: Путь к аудиофайлу
    :param language_code: Код языка (ru, en, de, fr) или 'auto' для автоопределения
    :param target_language: Опциональный код языка назначения для улучшения распознавания
    :return: Распознанный текст
    """
    # Конвертируем аудио в нужный формат
    temp_path = convert_audio(audio_file)
    enhanced_path = None
    
    try:
        if language_code == 'auto':
            # Автоматическое определение языка
            language_code, enhanced_path = detect_language(temp_path)
            print(f"Определен язык: {language_code}")
        
        model_data = get_model_for_language(language_code)
        processor = model_data['processor']
        model = model_data['model']
        sample_rate = model_data['sample_rate']

        if not enhanced_path:
            # Предварительная обработка аудио
            enhanced_path = preprocess_audio(temp_path, target_sr=sample_rate)
        
        # Загрузка и обработка аудио
        waveform, sr = librosa.load(enhanced_path, sr=sample_rate, mono=True)
        waveform = librosa.util.normalize(waveform)

        # Распознавание речи
        inputs = processor(waveform, sampling_rate=sample_rate, return_tensors="pt", padding=True)
        with torch.no_grad():
            logits = model(**inputs).logits
        predicted_ids = torch.argmax(logits, dim=-1)
        recognized_text = processor.batch_decode(predicted_ids)[0]
        
        # Постобработка текста
        recognized_text = postprocess_text(recognized_text, language_code)
        
        return recognized_text
        
    finally:
        # Удаление временных файлов
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        if enhanced_path and os.path.exists(enhanced_path):
            os.unlink(enhanced_path)
