"""
Точка входа приложения
"""
import sys
import logging
from pathlib import Path
import socket

# Определяем рабочую директорию
if getattr(sys, 'frozen', False):
    # Если упакован - логи ВНУТРИ временной папки
    WORK_DIR = Path(sys._MEIPASS)
else:
    # Если из исходников - текущая папка
    WORK_DIR = Path(__file__).parent

# Настройка логирования (ВНУТРИ)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(WORK_DIR / 'bot_session.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Файл блокировки - тоже внутри
LOCK_FILE = WORK_DIR / "bot.lock"

def check_single_instance():
    """Проверить что запущен только один экземпляр"""
    global LOCK_SOCKET
    
    # Используем socket вместо файла (работает на всех ОС)
    try:
        LOCK_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        LOCK_SOCKET.bind(('127.0.0.1', 47200))  # Уникальный порт для приложения
        logging.info("Первый экземпляр - запуск приложения")
        return True
    except socket.error:
        logging.warning("Приложение уже запущено - попытка активировать окно")
        
        # Попытка отправить сигнал запущенному экземпляру
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(('127.0.0.1', 47200))
            client.send(b'SHOW_WINDOW')
            client.close()
            logging.info("Сигнал отправлен запущенному экземпляру")
        except:
            logging.error("Не удалось связаться с запущенным экземпляром")
        
        return False

def remove_lock_file():
    """Удалить файл блокировки"""
    global LOCK_SOCKET
    if LOCK_SOCKET:
        try:
            LOCK_SOCKET.close()
        except:
            pass
        LOCK_SOCKET = None
    
    if LOCK_FILE.exists():
        LOCK_FILE.unlink()
        logging.info("Lock file removed")

if __name__ == '__main__':
    try:
        # Проверка single instance
        if not check_single_instance():
            print("❌ Приложение уже запущено! Активирую существующее окно...")
            sys.exit(0)
        
        # Импорты (после проверки блокировки)
        from characters.manager import MultiboxManager
        from config.settings import SettingsManager
        from gui import MainWindow
        
        logging.info("=== Запуск приложения ===")
        
        # Создание менеджеров
        settings_manager = SettingsManager()
        multibox_manager = MultiboxManager()
        
        # Создание и запуск GUI
        app = MainWindow(multibox_manager, settings_manager)
        
        # Запустить слушатель для сигналов от других экземпляров
        app.start_instance_listener()
        
        logging.info("GUI инициализирован")
        
        # Запуск главного цикла
        app.run()
        
    except KeyboardInterrupt:
        logging.info("Interrupted by user")
    except Exception as e:
        logging.error(f"Fatal error: {e}", exc_info=True)
    finally:
        # Очистка
        remove_lock_file()
        logging.info("=== Завершение приложения ===")