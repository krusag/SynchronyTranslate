# app/utils.py
# Утилитарные функции для обработки аудио

from pydub import AudioSegment
import tempfile
import os
from pydub.utils import which

# Указываем путь к ffmpeg
AudioSegment.converter = which("ffmpeg") or "ffmpeg.exe"

def convert_audio(audio_file):
    """
    Конвертирует аудиофайл в формат .wav для распознавания.
    Принимает файл (webm/ogg) и возвращает путь к временно сохранённому файлу.
    """
    if not audio_file:
        raise ValueError("Аудиофайл не выбран.")

    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_out:
        audio = AudioSegment.from_file(audio_file, format="webm")
        audio = audio.set_channels(1).set_frame_rate(16000)
        audio.export(tmp_out.name, format="wav")
        return tmp_out.name
