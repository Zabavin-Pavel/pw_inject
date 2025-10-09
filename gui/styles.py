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
WINDOW_WIDTH = 450
WINDOW_HEIGHT = 550

# Шрифты (УМЕНЬШЕНЫ)
FONT_MAIN = ("Segoe UI", 10)       # Было 14
FONT_TITLE = ("Segoe UI", 12, "bold")  # Было 13
FONT_HOTKEY = ("Segoe UI", 10)     # Было 13

# Размеры иконок
ICON_SIZE = 20
ICON_SIZE_BUTTON = 24

# Ширина панелей
CHARACTERS_PANEL_WIDTH = 190
HOTKEY_ACTION_WIDTH = 160
HOTKEY_INPUT_WIDTH = 70

# Пути
ASSETS_PATH = "assets"
ICONS_PATH = f"{ASSETS_PATH}/class_icons"
TRAY_ICON_PATH = f"{ASSETS_PATH}/icon.png"
SETTINGS_FILE = "settings.json"
LOG_FILE = "bot_session.log"

# Максимальная длина имени
MAX_NAME_LENGTH = 20
MAX_ACTION_LENGTH = 25

# Файл блокировки
LOCK_FILE = "bot.lock"