"""
Менеджер настроек приложения
ОБНОВЛЕНО: Все файлы (settings.json) в AppData
"""
import json
import logging
from pathlib import Path
import sys

class SettingsManager:
    """Менеджер настроек приложения (UI, хоткеи, позиция окна)"""
    
    def __init__(self, settings_file="settings.json"):
        # AppData папка (всегда - и для dev и для prod)
        # C:\Users\USERNAME\AppData\Local\xvocmuk\
        self.appdata_dir = Path.home() / "AppData" / "Local" / "xvocmuk"
        self.appdata_dir.mkdir(parents=True, exist_ok=True)
        
        # settings.json ВСЕГДА в AppData
        self.settings_file = self.appdata_dir / settings_file
        
        # Флаг режима (для отладки)
        self.is_frozen = getattr(sys, 'frozen', False)
        
        logging.info(f"📁 Settings file: {self.settings_file}")
        
        self.settings = self._load_settings()
    
    def _load_settings(self):
        """Загрузить настройки из файла"""
        if not self.settings_file.exists():
            logging.info("⚠️ Settings file not found, creating default")
            default_settings = self._get_default_settings()
            self._save_settings(default_settings)
            return default_settings
        
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                logging.info(f"✅ Settings loaded from {self.settings_file}")
                return settings
        except Exception as e:
            logging.error(f"❌ Failed to load settings: {e}")
            return self._get_default_settings()
    
    def _get_default_settings(self):
        """Получить настройки по умолчанию"""
        return {
            "window_position": {"x": 100, "y": 100},
            "is_topmost": False,
            "hotkeys": {
                # TRY
                "ahk_click_mouse": "-",
                "ahk_press_space": "-",
                "ahk_follow_lider": "-",
                # PRO
                "separator_pro": "-",
                "tp_to_target": "-",
                "tp_next": "-",
                "tp_long_left": "-",
                "tp_long_right": "-",
                "tp_exit": "-",
                # DEV
                "separator_dev": "-",
                "tp_to_so": "-",
                "tp_to_go": "-",
            }
        }
    
    def _save_settings(self, settings):
        """Сохранить настройки напрямую (внутренний метод)"""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logging.error(f"❌ Failed to save settings: {e}")
    
    def save(self):
        """Сохранить текущие настройки в файл"""
        self._save_settings(self.settings)
        logging.info("✅ Settings saved")
    
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