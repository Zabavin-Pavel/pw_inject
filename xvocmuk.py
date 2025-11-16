"""
Главный файл приложения xvocmuk
Мультибокс бот для Perfect World
"""
import sys
import logging
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('xvocmuk.log', encoding='utf-8')
    ]
)

# Импорты модулей приложения
from core.app_hub import AppHub


class XvocmukApp:
    """Главное приложение мультибокса"""
    
    VERSION = "8"
    APP_NAME = "xvocmuk"
    
    def __init__(self):
        """Инициализация приложения"""
        self.app_hub = None
        self.base_address = None
        
        logging.info("=" * 60)
        logging.info("XVOCMUK MULTIBOX BOT")
        logging.info("=" * 60)
    
    def initialize(self) -> bool:
        """
        Инициализация всех компонентов
        
        Returns:
            bool: успешность инициализации
        """
        # 1. Инициализация AppHub и проверка лицензии
        if not self._initialize_apphub():
            return False
        
        # 2. Загрузка base_address из конфигурации
        if not self._load_base_address():
            return False
        
        logging.info("✅ Application initialized successfully")
        return True
    
    def _initialize_apphub(self) -> bool:
        """Инициализация AppHub и проверка лицензии"""
        try:
            logging.info("🔐 Checking license...")
            
            # Создаем AppHub
            self.app_hub = AppHub(
                app_name=self.APP_NAME,
                current_version=self.VERSION,
                timeout=10
            )
            
            # Проверяем лицензию
            license_level = self.app_hub.check_license()
            
            if license_level is None:
                logging.error("❌ License check failed")
                return False
            
            logging.info(f"✅ License: {license_level}")
            
            return True
            
        except Exception as e:
            logging.error(f"❌ Error initializing AppHub: {e}")
            return False
    
    def _load_base_address(self) -> bool:
        """Загрузка base_address из AppHub"""
        try:
            logging.info("📋 Loading base_address from config...")
            
            # Получаем base_address из конфига
            base_address_str = self.app_hub.get('base_address')
            if not base_address_str:
                logging.error("❌ base_address not found in config")
                return False
            
            # Конвертируем hex строку в int
            if isinstance(base_address_str, str):
                self.base_address = int(base_address_str, 16) if base_address_str.startswith('0x') else int(base_address_str)
            else:
                self.base_address = base_address_str
            
            logging.info(f"✅ Base address: {hex(self.base_address)}")
            
            return True
            
        except Exception as e:
            logging.error(f"❌ Error loading base_address: {e}")
            return False
    
    def run(self):
        """Запуск приложения"""
        logging.info("🚀 Starting application...")
        
        # Импорты GUI компонентов
        from characters.manager import MultiboxManager
        from config.settings import SettingsManager
        from gui import MainWindow
        
        # Создание менеджеров
        settings_manager = SettingsManager()
        multibox_manager = MultiboxManager()
        
        # Передаем base_address в multibox_manager
        multibox_manager.base_address = self.base_address
        
        # Создание и запуск GUI
        gui_app = MainWindow(multibox_manager, settings_manager)
        
        # Запустить слушатель для сигналов от других экземпляров
        gui_app.start_instance_listener()
        
        logging.info("GUI инициализирован")
        
        # Запуск главного цикла tkinter
        gui_app.run()
    
    def shutdown(self):
        """Завершение работы приложения"""
        logging.info("🛑 Shutting down...")
        logging.info("✅ Shutdown complete")


def main():
    """Точка входа приложения"""
    try:
        app = XvocmukApp()
        
        if not app.initialize():
            logging.error("❌ Failed to initialize application")
            sys.exit(1)
        
        app.run()
        
    except Exception as e:
        logging.error(f"❌ Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()