"""
Стили и константы для GUI
"""
import sys
from pathlib import Path

# Цвета (оранжевая тема)
COLOR_BG = "#1a1a1a"
COLOR_BG_LIGHT = "#2b2b2b"
COLOR_TEXT = "#b0b0b0"
COLOR_TEXT_BRIGHT = "#b0b0b0"
COLOR_ACCENT = "#ff8c42"        # Оранжевый основной
COLOR_ACCENT_HOVER = "#ffa050"  # Светло-оранжевый при наведении
COLOR_BORDER = "#3a3a3a"
COLOR_SELECTED = "#ffa050"      # Светло-оранжевый для выделения

# Размеры окна
WINDOW_WIDTH = 320
WINDOW_HEIGHT = 360
# Шрифты
FONT_MAIN = ("Consolas", 9)
FONT_TITLE = ("Consolas", 14, "bold")
FONT_HOTKEY = ("semibold", 8, "bold")

# Размеры иконок
ICON_SIZE = 15
ICON_SIZE_BUTTON = 24

# Ширина панелей
CHARACTERS_PANEL_WIDTH = 110
HOTKEY_ACTION_WIDTH = 150

# Пути к ресурсам
if getattr(sys, 'frozen', False):
    # Упакованное приложение - ресурсы внутри EXE
    ASSETS_PATH = str(Path(sys._MEIPASS) / "assets")
else:
    # Исходники
    ASSETS_PATH = "assets"

ICONS_PATH = f"{ASSETS_PATH}/class_icons"
TRAY_ICON_PATH = f"{ASSETS_PATH}/icon.png"

# Файлы настроек
SETTINGS_FILE = "settings.json"
LOG_FILE = "bot_session.log"

# Максимальная длина имени
MAX_NAME_LENGTH = 13
MAX_ACTION_LENGTH = 22

# Файл блокировки
LOCK_FILE = "bot.lock"

def hotkey_to_short_format(hotkey: str) -> str:
    """
    Преобразовать хоткей в короткий формат для отображения
    Shift+A → +A
    Ctrl+S → ^S
    Alt+T → *T
    Ctrl+Shift+X → ^+X
    """
    if not hotkey or hotkey == "-":
        return hotkey
    
    parts = hotkey.split('+')
    result = []
    
    for part in parts:
        part_lower = part.lower()
        
        if part_lower == 'shift':
            result.append('Shift+')
        elif part_lower == 'ctrl':
            result.append('Ctrl+')
        elif part_lower == 'alt':
            result.append('Alt+')
        else:
            # Обычная клавиша
            result.append(part)
    
    return ''.join(result)


def hotkey_to_full_format(short_hotkey: str) -> str:
    """
    Преобразовать короткий формат обратно в полный
    +A → Shift+A
    ^S → Ctrl+S
    *T → Alt+T
    ^+X → Ctrl+Shift+X
    """
    if not short_hotkey or short_hotkey == "-":
        return short_hotkey
    
    result = []
    i = 0
    
    while i < len(short_hotkey):
        char = short_hotkey[i]
        
        if char == 'Shift':
            result.append('Shift')
        elif char == 'Ctrl':
            result.append('Ctrl')
        elif char == 'Alt':
            result.append('Alt')
        else:
            # Обычная клавиша (может быть несколько символов, например F1)
            key = char
            j = i + 1
            while j < len(short_hotkey) and short_hotkey[j] not in ['Shift', 'Ctrl', 'Alt']:
                key += short_hotkey[j]
                j += 1
            result.append(key)
            i = j - 1
        
        i += 1
    
    return '+'.join(result)