"""
Менеджер настроек
"""
import json
import logging
from pathlib import Path

class SettingsManager:
    """Менеджер настроек приложения"""
    
    def __init__(self, settings_file="settings.json"):
        self.settings_file = Path(settings_file)
        self.settings = self._load_settings()
    
    def _load_settings(self):
        """Загрузить настройки из файла"""
        if not self.settings_file.exists():
            logging.info("Settings file not found, creating default")
            return self._get_default_settings()
        
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                logging.info("Settings loaded")
                return settings
        except Exception as e:
            logging.error(f"Failed to load settings: {e}")
            return self._get_default_settings()
    
    def _get_default_settings(self):
        """Получить настройки по умолчанию"""
        return {
            "hwid": "",
            "key": "",
            "window_position": {"x": 100, "y": 100},
            "is_topmost": False,
            "hotkeys": {
                "show_all": "Shift+U",
                "show_active": "Shift+Y",
                "show_loot": "-",
                "show_players": "-",
                "show_npcs": "-"
            }
        }
    
    def save(self):
        """Сохранить настройки в файл"""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
            logging.info("Settings saved")
        except Exception as e:
            logging.error(f"Failed to save settings: {e}")
    
    def get_hwid(self) -> str:
        """Получить сохранённый HWID"""
        return self.settings.get("hwid", "")
    
    def set_hwid(self, hwid: str):
        """Установить HWID"""
        self.settings["hwid"] = hwid
        self.save()
    
    def get_license_key(self) -> str:
        """Получить лицензионный ключ"""
        return self.settings.get("key", "")
    
    def set_license_key(self, key: str):
        """Установить лицензионный ключ"""
        self.settings["key"] = key
        self.save()
    
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