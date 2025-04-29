# app/speech_recognition.py

import os
import torch
import librosa
from transformers import Wav2Vec2Processor, Wav2Vec2ForCTC
from app.utils import convert_audio

HF_MODEL_ID = "jonatasgrosman/wav2vec2-large-xlsr-53-russian"
MODEL_CACHE_DIR = "./models/wav2vec_ru"

# Скачивание модели (один раз)
def download_model_if_needed():
    if not os.path.exists(MODEL_CACHE_DIR):
        os.makedirs(MODEL_CACHE_DIR, exist_ok=True)
    # Проверим папку вручную, иначе всегда будет качать заново
    local_model_dir = os.path.join(
        MODEL_CACHE_DIR, HF_MODEL_ID.replace("/", os.sep)
    )
    if not os.path.exists(local_model_dir):
        print("⏬ Скачиваем wav2vec2 модель...")
        Wav2Vec2Processor.from_pretrained(HF_MODEL_ID, cache_dir=MODEL_CACHE_DIR)
        Wav2Vec2ForCTC.from_pretrained(HF_MODEL_ID, cache_dir=MODEL_CACHE_DIR)
        print("✅ Модель загружена.")
    else:
        print("✅ wav2vec2 модель найдена локально.")

download_model_if_needed()

# Загружаем из оригинального ID, указывая cache_dir
processor = Wav2Vec2Processor.from_pretrained(HF_MODEL_ID, cache_dir=MODEL_CACHE_DIR)
model = Wav2Vec2ForCTC.from_pretrained(HF_MODEL_ID, cache_dir=MODEL_CACHE_DIR)
model.eval()

def recognize_speech(audio_file):
    """
    Распознаёт речь из аудиофайла и возвращает текст.
    """
    temp_path = convert_audio(audio_file)

    waveform, sr = librosa.load(temp_path, sr=16000, mono=True)
    waveform = librosa.util.normalize(waveform)

    inputs = processor(waveform, sampling_rate=16000, return_tensors="pt", padding=True)
    with torch.no_grad():
        logits = model(**inputs).logits
    predicted_ids = torch.argmax(logits, dim=-1)
    recognized_text = processor.batch_decode(predicted_ids)[0]

    os.unlink(temp_path)

    return recognized_text
