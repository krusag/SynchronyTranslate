# Импортирование библиотек
import speech_recognition as sr
from deep_translator import GoogleTranslator
import pyttsx3
import tkinter as tk
from threading import Thread, Lock
import queue
import torch
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
import logging
import wave
from flask import Flask, request, jsonify, render_template  # Добавляем Flask и render_template

# Инициализируем компоненты
engine = pyttsx3.init()

# Флаг для управления процессом записи
is_recording = False

# Кэш для хранения уже переведенных фраз
translation_cache = {}

# Параметры аудио
samplerate = 16000
device = torch.device("cpu")  # Используем CPU

# Загрузка модели Wav2Vec 2.0
try:
    model_path = "C:/Users/Admin/PycharmProjects/pythonProject1/wav2vec2-base-960h"  # Используем более универсальную модель
    processor = Wav2Vec2Processor.from_pretrained(model_path)
    model = Wav2Vec2ForCTC.from_pretrained(model_path).to(device)
except Exception as e:
    print(f"Ошибка при загрузке модели: {e}")
    exit(1)

# Очередь для хранения текста для синтеза речи
speech_queue = queue.Queue()
speech_lock = Lock()
recognizer = sr.Recognizer()

# Логирование
logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')

# Глобальные переменные для хранения текста и языка перевода
recognized_text = ""
translated_text = ""
target_language = "en"  # Язык перевода по умолчанию

# Инициализация Flask приложения
app = Flask(__name__)

# Функция для вывода сообщений в текстовое поле и лог
def log_message(message):
    text_widget.insert(tk.END, f"{message}\n")
    text_widget.see(tk.END)
    logging.info(message)

# Функция для сохранения аудио в файл
def save_audio_to_file(filename, data):
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(1)  # Одна аудиоканал
        wf.setsampwidth(2)  # 16-bit PCM
        wf.setframerate(samplerate)
        wf.writeframes(data.tobytes())

# Функция для записи аудио с микрофона
def record_audio():
    global is_recording, recognized_text, translated_text, target_language
    print("Начало прослушивания... Говорите что-нибудь...")
    text_widget.insert(tk.END, "Начало прослушивания... Говорите что-нибудь...\n")
    text_widget.see(tk.END)

    while is_recording:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)  # Адаптация к фоновому шуму
            try:
                # Записываем аудио с микрофона
                audio = recognizer.listen(source, timeout=2)
                # Распознаем речь с помощью Google Speech-to-Text API
                text = recognizer.recognize_google(audio, language=source_language.get())
                recognized_text = text  # Сохраняем распознанный текст
                print(f"Распознанный текст: {text}")  # Выводим распознанный текст
                text_widget.insert(tk.END, f"Распознанный текст: {text}\n")
                text_widget.see(tk.END)

                # Переводим текст
                translated_text = translate_text(text, target_language)
                if translated_text:
                    speak_text(translated_text)  # Озвучиваем переведённый текст
                    text_widget.insert(tk.END, f"Переведенный текст: {translated_text}\n")
                    text_widget.see(tk.END)
            except sr.UnknownValueError:
                # Обрабатываем ошибку, если речь не распознана
                recognized_text = "Не удалось распознать речь"
                print("Не удалось распознать речь")
                text_widget.insert(tk.END, "Не удалось распознать речь\n")
                text_widget.see(tk.END)
            except sr.WaitTimeoutError:
                # Обрабатываем ошибку таймаута (если нет звука в течение некоторого времени)
                pass
            except sr.RequestError as e:
                # Обрабатываем ошибку, если запрос к сервису распознавания речи не удался
                recognized_text = f"Ошибка сервиса распознавания речи: {e}"
                print(f"Ошибка сервиса распознавания речи; {e}")
                text_widget.insert(tk.END, f"Ошибка сервиса распознавания речи; {e}\n")
                text_widget.see(tk.END)

# Функция для перевода текста
def translate_text(text, dest_language='en'):
    cache_key = (text, source_language.get(), dest_language)
    if cache_key in translation_cache:
        return translation_cache[cache_key]

    try:
        # Переводим текст на целевой язык
        translator = GoogleTranslator(source=source_language.get(), target=dest_language)
        translated_text = translator.translate(text)
        print(f"Переведенный текст: {translated_text}")  # Выводим переведенный текст

        # Сохраняем результат в кэше
        translation_cache[cache_key] = translated_text

        return translated_text  # Возвращаем переведенный текст
    except Exception as e:
        log_message(f"Ошибка перевода: {e}")
        return ""

# Функция для генерации речи из текста
def speak_text(text):
    with speech_lock:
        speech_queue.put(text)
        if not hasattr(speak_text, "_thread") or not speak_text._thread.is_alive():
            speak_text._thread = Thread(target=run_speech)
            speak_text._thread.start()

def run_speech():
    while not speech_queue.empty():
        text = speech_queue.get()
        engine.say(text)
        engine.runAndWait()

# Функция для запуска записи
def start_recording():
    global is_recording
    if not is_recording:
        is_recording = True
        recording_thread = Thread(target=record_audio)
        recording_thread.start()
        log_message("Запись начата")

# Функция для остановки записи
def stop_recording():
    global is_recording
    if is_recording:
        is_recording = False
        log_message("Запись остановлена")

# Функция для очистки текстового поля
def clear_text():
    text_widget.delete(1.0, tk.END)

# Функция для настройки громкости синтезатора речи
def set_volume(volume_level):
    try:
        volume_level = float(volume_level)  # Преобразуем значение в число с плавающей точкой
        engine.setProperty('volume', volume_level / 100.0)
    except ValueError:
        log_message("Ошибка: Некорректное значение громкости")

# Функция для настройки скорости синтезатора речи
def set_rate(rate_value):
    try:
        rate_value = int(rate_value)  # Преобразуем значение в целое число
        engine.setProperty('rate', rate_value)
    except ValueError:
        log_message("Ошибка: Некорректное значение скорости")

# Функция для сохранения логов в файл
def save_logs():
    with open('app.log', 'r') as file:
        logs = file.read()
    with open('saved_app.log', 'w') as file:
        file.write(logs)
    log_message("Логи сохранены в файл saved_app.log")

def stop_program():
    global is_recording
    if is_recording:
        is_recording = False
    root.quit()  # Закрываем главное окно
    root.destroy()

# Создаем графический интерфейс
root = tk.Tk()
root.title("Real-time Translator")

# Текстовое поле для вывода информации
text_widget = tk.Text(root, wrap=tk.WORD, height=20, width=80)
text_widget.pack(pady=10)

# Кнопка для начала записи
start_button = tk.Button(root, text="Начать запись", command=start_recording)
start_button.pack(side=tk.LEFT, padx=10)

# Кнопка для остановки записи
stop_button = tk.Button(root, text="Остановить запись", command=stop_recording)
stop_button.pack(side=tk.RIGHT, padx=10)

# Кнопка для очистки текстового поля
clear_button = tk.Button(root, text="Очистить текст", command=clear_text)
clear_button.pack(side=tk.LEFT, padx=10)

# Кнопка для сохранения логов
save_logs_button = tk.Button(root, text="Сохранить логи", command=save_logs)
save_logs_button.pack(side=tk.RIGHT, padx=10)

# Ползунок для регулировки громкости синтезатора речи
volume_scale = tk.Scale(root, from_=0, to=100, orient=tk.HORIZONTAL, label="Громкость",
                        command=lambda value: set_volume(value))
volume_scale.set(50)  # Устанавливаем громкость по умолчанию
volume_scale.pack(pady=10)

# Ползунок для регулировки скорости синтезатора речи
rate_scale = tk.Scale(root, from_=50, to=300, orient=tk.HORIZONTAL, label="Скорость",
                      command=lambda value: set_rate(value))
rate_scale.set(150)  # Устанавливаем скорость по умолчанию
rate_scale.pack(pady=10)

# Выпадающий список для выбора исходного языка
source_languages = ['ru', 'en', 'es', 'fr', 'de']  # Пример списка языков
source_language = tk.StringVar(value='ru')
source_language_menu = tk.OptionMenu(root, source_language, *source_languages)
source_language_menu.pack(pady=10)

# Выпадающий список для выбора целевого языка
dest_languages = ['en', 'ru', 'es', 'fr', 'de']  # Пример списка языков
dest_language = tk.StringVar(value='en')
dest_language_menu = tk.OptionMenu(root, dest_language, *dest_languages)
dest_language_menu.pack(pady=10)

# Кнопка остановки программы
stop_program_button = tk.Button(root, text="Остановить программу", command=stop_program)
stop_program_button.pack(pady=10)

# Очередь для хранения аудио данных
q = queue.Queue()

# Эндпоинты API
@app.route('/')
def index():
    return render_template('index.html')  # Отображаем HTML-шаблон

@app.route('/start', methods=['POST'])
def api_start_recording():
    start_recording()
    return jsonify({"status": "Recording started"})

@app.route('/stop', methods=['POST'])
def api_stop_recording():
    stop_recording()
    return jsonify({"status": "Recording stopped"})

@app.route('/get_text', methods=['GET'])
def get_text():
    return jsonify({
        "recognized_text": recognized_text,
        "translated_text": translated_text
    })

@app.route('/set_language', methods=['POST'])
def set_language():
    global target_language
    data = request.json
    target_language = data.get('language', 'en')
    return jsonify({"status": f"Язык перевода изменён на {target_language}"})

@app.route('/speak_translated', methods=['POST'])
def speak_translated():
    speak_text(translated_text)
    return jsonify({"status": "Переведённый текст озвучен"})

# Запуск Flask приложения в отдельном потоке
flask_thread = Thread(target=app.run, kwargs={'host': '0.0.0.0', 'port': 5000})
flask_thread.start()

# Запуск главного цикла приложения
root.mainloop()