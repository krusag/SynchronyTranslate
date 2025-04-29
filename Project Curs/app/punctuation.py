# app/punctuation.py
# Модуль для восстановления пунктуации в тексте

from deepmultilingualpunctuation import PunctuationModel

# Загружаем локальную модель пунктуации
punct_model = PunctuationModel()

def punctuate_text(text):
    """
    Восстанавливает пунктуацию в тексте.
    """
    return punct_model.restore_punctuation(text)
