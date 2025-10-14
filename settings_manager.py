"""
Менеджер настроек приложения (БЕЗ лицензий)
"""
import json
import logging
from pathlib import Path
import sys

class SettingsManager:
    """Менеджер настроек приложения (UI, хоткеи, позиция окна)"""
    
    def __init__(self, settings_file="settings.json"):
        # Определяем путь к settings.json
        if getattr(sys, 'frozen', False):
            # Если запущен из EXE - settings.json внутри EXE (temporary folder)
            self.settings_file = Path(sys._MEIPASS) / settings_file
            self.is_frozen = True
        else:
            # Если запущен из исходников - рядом с bot.py
            self.settings_file = Path(settings_file)
            self.is_frozen = False
        
        self.settings = self._load_settings()
    
    def _load_settings(self):
        """Загрузить настройки из файла"""
        if not self.settings_file.exists():
            logging.info("Settings file not found, using default")
            return self._get_default_settings()
        
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                logging.info(f"Settings loaded from {self.settings_file}")
                return settings
        except Exception as e:
            logging.error(f"Failed to load settings: {e}")
            return self._get_default_settings()
    
    def _get_default_settings(self):
        """Получить настройки по умолчанию"""
        return {
            "window_position": {"x": 100, "y": 100},
            "is_topmost": False,
            "hotkeys": {
                "teleport_to_target": "-",
                "show_all": "-",
                "show_active": "-",
                "show_loot": "-",
                "show_players": "-",
                "show_npcs": "-",
                "ahk_click_mouse": "-",
                "ahk_press_space": "-"
            }
        }
    
    def save(self):
        """
        Сохранить настройки в файл
        
        ВАЖНО: Если приложение запущено из EXE (frozen),
        settings.json находится внутри временной папки и не сохраняется.
        Настройки восстанавливаются из дефолтных при каждом запуске.
        """
        if self.is_frozen:
            # Внутри EXE - не сохраняем (временная папка)
            logging.debug("Settings not saved (running from EXE)")
            return
        
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
            logging.info("Settings saved")
        except Exception as e:
            logging.error(f"Failed to save settings: {e}")
    
    def get_hotkeys(self) -> dict:
        """Получить хоткеи"""
        return self.settings.get("hotkeys", {})
    
    def set_hotkeys(self, hotkeys: dict):
        """Установить хоткеи"""
        self.settings["hotkeys"] = hotkeys
        self.save()
    
    def get_window_position(self) -> dict:
        """Получить позицию окна"""
        return self.settings.get("window_position", {"x": 100, "y": 100})
    
    def set_window_position(self, x: int, y: int):
        """Установить позицию окна"""
        self.settings["window_position"] = {"x": x, "y": y}
        self.save()
    
    def is_topmost(self) -> bool:
        """Проверить режим поверх всех окон"""
        return self.settings.get("is_topmost", False)
    
    def set_topmost(self, topmost: bool):
        """Установить режим поверх всех окон"""
        self.settings["is_topmost"] = topmost
        self.save()