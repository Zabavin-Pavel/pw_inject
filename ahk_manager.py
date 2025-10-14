"""
Менеджер AHK - запускает и управляет hotkeys.exe
"""
import subprocess
import sys
import time
import atexit
import logging
from pathlib import Path
import shutil

class AHKManager:
    """Управляет постоянным AHK процессом"""
    
    def __init__(self):
        # Определяем пути
        if getattr(sys, 'frozen', False):
            # Если упакован в EXE
            temp_dir = Path(sys._MEIPASS)
            
            # AppData папка для хранения hotkeys.exe
            appdata_dir = Path.home() / "AppData" / "Local" / "xvocmuk"
            appdata_dir.mkdir(parents=True, exist_ok=True)
            
            # hotkeys.exe в AppData (скрыто, но постоянно)
            self.ahk_exe = appdata_dir / "hotkeys.exe"
            
            # Копируем из ресурсов в AppData (ВСЕГДА перезаписываем - обновление)
            bundled_ahk = temp_dir / "hotkeys.exe"
            if bundled_ahk.exists():
                shutil.copy(bundled_ahk, self.ahk_exe)
                logging.info(f"Deployed hotkeys.exe to {self.ahk_exe}")
            
            # ahk_command.txt - ВНУТРИ временной папки
            self.command_file = temp_dir / "ahk_command.txt"
        else:
            # Если из исходников
            base_path = Path(__file__).parent
            self.ahk_exe = base_path / "hotkeys.exe"
            self.command_file = base_path / "ahk_command.txt"
        
        self.process = None
        
        # Запускаем AHK при создании
        self.start()
        
        # Регистрируем остановку при выходе
        atexit.register(self.stop)
    
    def start(self):
        """Запустить AHK процесс"""
        if not self.ahk_exe.exists():
            logging.error(f"AHK not found: {self.ahk_exe}")
            return False
        
        # Удаляем старый файл команд перед запуском
        if self.command_file.exists():
            try:
                self.command_file.unlink()
            except:
                pass
        
        try:
            # ВАЖНО: Передаем путь к command_file как аргумент
            self.process = subprocess.Popen(
                [str(self.ahk_exe), str(self.command_file)],
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            logging.info(f"AHK started (PID: {self.process.pid})")
            logging.info(f"Command file: {self.command_file}")
            
            # Даём AHK время на инициализацию
            time.sleep(0.5)
            
            return True
        except Exception as e:
            logging.error(f"Failed to start AHK: {e}")
            return False
    
    def send_command(self, command: str):
        """Отправить команду в AHK"""
        if not self.process or self.process.poll() is not None:
            logging.warning("AHK not running, restarting...")
            self.start()
            time.sleep(0.5)
        
        try:
            # Ждём пока файл освободится
            max_wait = 0.5
            wait_step = 0.05
            waited = 0
            
            while self.command_file.exists() and waited < max_wait:
                time.sleep(wait_step)
                waited += wait_step
            
            # Записываем команду в файл
            self.command_file.write_text(command, encoding='utf-8')
            
            # Небольшая задержка
            time.sleep(0.05)
            
            return True
        except Exception as e:
            logging.error(f"Failed to send command: {e}")
            return False
    
    def click_at_mouse(self):
        """Кликнуть во всех окнах в текущей позиции мыши"""
        return self.send_command("CLICK")
    
    def send_key(self, key: str):
        """Отправить клавишу во все окна"""
        return self.send_command(f"KEY:{key}")
    
    def refresh_windows(self):
        """Обновить список окон в AHK"""
        logging.info("Refreshing AHK window list")
        return self.send_command("REFRESH")
    
    def stop(self):
        """Остановить AHK процесс"""
        if self.process and self.process.poll() is None:
            try:
                self.send_command("EXIT")
                self.process.wait(timeout=2)
                logging.info("AHK stopped gracefully")
            except subprocess.TimeoutExpired:
                self.process.kill()
                logging.warning("AHK killed forcefully")
            except Exception as e:
                logging.warning(f"Error stopping AHK: {e}")