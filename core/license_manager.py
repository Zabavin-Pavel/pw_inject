"""
Менеджер лицензий - работа с license.ini
ОБНОВЛЕНО: license.ini в AppData
"""
import configparser
import logging
from pathlib import Path
import sys
from core.keygen import get_mac_address

class LicenseConfig:
    """Управление файлом license.ini"""
    
    def __init__(self, license_file="license.ini"):
        # AppData папка (всегда - и для dev и для prod)
        # C:\Users\USERNAME\AppData\Local\xvocmuk\
        self.appdata_dir = Path.home() / "AppData" / "Local" / "xvocmuk"
        self.appdata_dir.mkdir(parents=True, exist_ok=True)
        
        # license.ini ВСЕГДА в AppData
        self.license_file = self.appdata_dir / license_file
        
        logging.info(f"📄 License file: {self.license_file}")
        
        self.config = configparser.ConfigParser()
        self._load()
    
    def _load(self):
        """Загрузить license.ini"""
        if not self.license_file.exists():
            logging.info("⚠️ license.ini not found, creating default")
            self._create_default()
        
        try:
            self.config.read(self.license_file, encoding='utf-8')
            logging.info("✅ license.ini loaded")
        except Exception as e:
            logging.error(f"❌ Failed to load license.ini: {e}")
            self._create_default()
    
    def reload(self):
        """Перечитать license.ini с диска (для обновления ключа без перезапуска)"""
        self._load()
        logging.info("🔄 license.ini reloaded from disk")

    def _create_default(self):
        """Создать дефолтный license.ini"""
        self.config['License'] = {
            'hwid': get_mac_address(),
            'key': '',
            'ticket': ''
        }
        self._save()
    
    def _save(self):
        """Сохранить license.ini"""
        try:
            with open(self.license_file, 'w', encoding='utf-8') as f:
                self.config.write(f)
            logging.info("✅ license.ini saved")
        except Exception as e:
            logging.error(f"❌ Failed to save license.ini: {e}")
    
    def get_hwid(self) -> str:
        """Получить HWID"""
        return self.config.get('License', 'hwid', fallback='')
    
    def set_hwid(self, hwid: str):
        """Установить HWID"""
        if 'License' not in self.config:
            self.config['License'] = {}
        self.config['License']['hwid'] = hwid
        self._save()
    
    def get_key(self) -> str:
        """Получить ключ"""
        return self.config.get('License', 'key', fallback='')
    
    def set_key(self, key: str):
        """Установить ключ"""
        if 'License' not in self.config:
            self.config['License'] = {}
        self.config['License']['key'] = key
        self._save()
    
    def get_ticket(self) -> str:
        """Получить талон"""
        return self.config.get('License', 'ticket', fallback='')
    
    def set_ticket(self, ticket: str):
        """Установить талон"""
        if 'License' not in self.config:
            self.config['License'] = {}
        self.config['License']['ticket'] = ticket
        self._save()