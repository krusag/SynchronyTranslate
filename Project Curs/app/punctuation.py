# app/punctuation.py
# Модуль для восстановления пунктуации в тексте

from deepmultilingualpunctuation import PunctuationModel
import re

# Загружаем локальную модель пунктуации
punct_model = PunctuationModel()

def punctuate_text(text, language_code=None):
    """
    Восстанавливает пунктуацию в тексте с учетом языка.
    """
    # Применяем основную модель
    punctuated_text = punct_model.restore_punctuation(text)
    
    # Дополнительные корректировки для разных языков
    if language_code:
        if language_code in ['ru', 'de']:
            # Исправление кавычек для русского и немецкого
            punctuated_text = re.sub(r'"([^"]*)"', r'«\1»', punctuated_text)
            
        if language_code == 'de':
            # Специфичные для немецкого правила
            punctuated_text = re.sub(r'\b([A-Za-z][a-z]*)\b', lambda m: m.group(1).capitalize() 
                                   if m.group(1) in ['ich', 'sie', 'es', 'er', 'wir', 'ihr'] else m.group(1), 
                                   punctuated_text)
            
        if language_code == 'fr':
            # Французские пробелы перед двоеточием и т.д.
            for char in [':', ';', '?', '!']:
                punctuated_text = re.sub(f'\\s*{char}', f' {char}', punctuated_text)
    
    # Общие корректировки
    # Убедиться, что после точки идет пробел
    punctuated_text = re.sub(r'\.([A-Za-zА-Яа-яÄäÖöÜüß])', r'. \1', punctuated_text)
    
    # Убедиться, что множественные пробелы заменены одним
    punctuated_text = re.sub(r'\s+', ' ', punctuated_text)
    
    # Убедиться, что первая буква текста заглавная
    if punctuated_text and punctuated_text[0].isalpha():
        punctuated_text = punctuated_text[0].upper() + punctuated_text[1:]
    
    return punctuated_text
