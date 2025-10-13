"""
Менеджер AHK - запускает и управляет hotkeys.exe
"""
import subprocess
import sys
import time
import atexit
import logging
from pathlib import Path

class AHKManager:
    """Управляет постоянным AHK процессом"""
    
    def __init__(self):
        # Определяем путь к папке
        if getattr(sys, 'frozen', False):
            self.base_path = Path(sys.executable).parent
        else:
            self.base_path = Path(__file__).parent
        
        self.ahk_exe = self.base_path / "hotkeys.exe"
        self.command_file = self.base_path / "ahk_command.txt"
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
        
        # НОВОЕ: Удаляем старый файл команд перед запуском
        if self.command_file.exists():
            try:
                self.command_file.unlink()
            except:
                pass
        
        try:
            self.process = subprocess.Popen(
                [str(self.ahk_exe)],
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            logging.info(f"AHK started (PID: {self.process.pid})")
            return True
        except Exception as e:
            logging.error(f"Failed to start AHK: {e}")
            return False
    
    def send_command(self, command: str):
        """
        Отправить команду в AHK
        
        Args:
            command: команда (CLICK, SPACE, KEY:F1, EXIT)
        """
        if not self.process or self.process.poll() is not None:
            logging.warning("AHK not running, restarting...")
            self.start()
            time.sleep(0.5)
        
        try:
            # Записываем команду в файл
            self.command_file.write_text(command, encoding='utf-8')
            
            # НОВОЕ: Небольшая задержка чтобы AHK успел прочитать
            time.sleep(0.1)
            
            return True
        except Exception as e:
            logging.error(f"Failed to send command: {e}")
            return False
    
    def click_at_mouse(self):
        """Кликнуть во всех окнах в текущей позиции мыши"""
        return self.send_command("CLICK")
    
    def send_key(self, key: str):
        """
        Отправить клавишу во все окна
        
        Args:
            key: клавиша (Space, F1, Ctrl+S, и т.д.)
        """
        return self.send_command(f"KEY:{key}")
    
    def stop(self):
        """Остановить AHK процесс"""
        if self.process and self.process.poll() is None:
            try:
                # Посылаем команду EXIT
                self.send_command("EXIT")
                
                # Ждём завершения
                self.process.wait(timeout=2)
                logging.info("AHK stopped gracefully")
            except subprocess.TimeoutExpired:
                # Если не остановился - убиваем
                self.process.kill()
                logging.warning("AHK killed forcefully")
            except Exception as e:
                logging.warning(f"Error stopping AHK: {e}")