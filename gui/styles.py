"""
Стили и константы для GUI
"""

# Цвета (оранжевая тема)
COLOR_BG = "#1a1a1a"
COLOR_BG_LIGHT = "#2b2b2b"
COLOR_TEXT = "#b0b0b0"
COLOR_TEXT_BRIGHT = "#ffffff"
COLOR_ACCENT = "#ff8c42"        # Оранжевый основной
COLOR_ACCENT_HOVER = "#ffa050"  # Светло-оранжевый при наведении
COLOR_BORDER = "#3a3a3a"
COLOR_SELECTED = "#ffa050"      # Светло-оранжевый для выделения

# Размеры окна
WINDOW_WIDTH = 370
WINDOW_HEIGHT = 400

# Шрифты (УМЕНЬШЕНЫ)
FONT_MAIN = ("Segoe UI", 10)       # Было 14
FONT_TITLE = ("Segoe UI", 12, "bold")  # Было 13
FONT_HOTKEY = ("Segoe UI", 10)     # Было 13

# Размеры иконок
ICON_SIZE = 20
ICON_SIZE_BUTTON = 24

# Ширина панелей
CHARACTERS_PANEL_WIDTH = 150
HOTKEY_ACTION_WIDTH = 160

# Пути
ASSETS_PATH = "assets"
ICONS_PATH = f"{ASSETS_PATH}/class_icons"
TRAY_ICON_PATH = f"{ASSETS_PATH}/icon.png"
SETTINGS_FILE = "settings.json"
LOG_FILE = "bot_session.log"

# Максимальная длина имени
MAX_NAME_LENGTH = 15
MAX_ACTION_LENGTH = 18

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
            result.append('ctrl')
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