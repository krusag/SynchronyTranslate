# app/audio_processing.py
# Функции для улучшения качества аудио перед распознаванием

import numpy as np
import librosa
import soundfile as sf
from scipy import signal

def enhance_audio(waveform, sample_rate):
    """
    Мягкая обработка аудио: только trim и нормализация.
    """
    # Нормализация
    waveform = librosa.util.normalize(waveform)
    
    # Удаление тишины в начале и конце
    waveform, _ = librosa.effects.trim(waveform, top_db=20)
    
    # Финальная нормализация
    waveform = librosa.util.normalize(waveform)
    
    return waveform

def remove_noise(waveform, sample_rate):
    """
    Отключено: возвращает исходный сигнал без изменений.
    """
    return waveform

def enhance_voice(waveform, sample_rate):
    """
    Отключено: возвращает исходный сигнал без изменений.
    """
    return waveform

def preprocess_audio(audio_path, target_sr=16000):
    """
    Предварительная обработка аудиофайла перед распознаванием.
    """
    # Загрузка аудио
    waveform, sr = librosa.load(audio_path, sr=None)
    
    # Ресемплинг если нужно
    if sr != target_sr:
        waveform = librosa.resample(waveform, orig_sr=sr, target_sr=target_sr)
        sr = target_sr
    
    # Улучшение качества
    enhanced_waveform = enhance_audio(waveform, sr)
    
    # Сохранение обработанного аудио
    temp_path = audio_path + '.enhanced.wav'
    sf.write(temp_path, enhanced_waveform, sr)
    
    return temp_path 