"""
Менеджер AHK - УПРОЩЕНО: без параметров
"""
import subprocess
import logging
from pathlib import Path
import time

class AHKManager:
    """Управление AutoHotkey скриптом"""
    
    def __init__(self):
        self.process = None
        appdata_dir = Path.home() / "AppData" / "Local" / "xvocmuk"
        appdata_dir.mkdir(parents=True, exist_ok=True)
        self.command_file = appdata_dir / "ahk_command.txt"
        
        # Запустить AHK
        self._start_ahk()
    
    def _start_ahk(self):
        """Запустить AHK процесс"""
        try:
            # Путь к скомпилированному hotkeys.exe
            ahk_exe = Path(__file__).parent / "hotkeys.exe"
            
            if not ahk_exe.exists():
                logging.error(f"❌ AHK exe not found: {ahk_exe}")
                return False
            
            logging.info(f"📁 AHK exe: {ahk_exe}")
            logging.info(f"📁 Command file: {self.command_file}")
            
            # Запустить AHK с путём к command_file
            self.process = subprocess.Popen(
                [str(ahk_exe), str(self.command_file)],
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            logging.info(f"✅ AHK started (PID: {self.process.pid})")
            
            # Небольшая пауза для инициализации
            time.sleep(0.1)
            
            return True
            
        except Exception as e:
            logging.error(f"❌ Failed to start AHK: {e}")
            return False
    
    def send_command(self, command: str):
        """
        Отправить команду в AHK через файл
        
        Args:
            command: команда для AHK
        
        Returns:
            bool: успешно ли отправлена команда
        """
        try:
            # Записать команду в файл
            with open(self.command_file, 'w', encoding='utf-8') as f:
                f.write(command)
            
            return True
            
        except Exception as e:
            logging.error(f"Failed to send AHK command '{command}': {e}")
            return False
    
    # === ПРОСТЫЕ КОМАНДЫ БЕЗ ПАРАМЕТРОВ ===
    
    def click_at_mouse(self):
        """Кликнуть по позиции курсора во всех окнах"""
        return self.send_command("CLICK")
    
    def send_space(self):
        """Отправить Space во все окна"""
        return self.send_command("SPACE")
    
    def follow_lider(self):
        """Follow - клик во всех окнах кроме активного"""
        return self.send_command("FOLLOW")
    
    def headhunter(self):
        """Headhunter - Tab + клик в активном окне"""
        return self.send_command("HEADHUNTER")
    
    def send_key(self, key: str):
        """
        Отправить клавишу во все окна
        
        Args:
            key: клавиша для отправки (W, A, S, D, etc)
        """
        return self.send_command(f"KEY:{key}")
    
    def refresh_windows(self):
        """Обновить список окон в AHK"""
        logging.info("🔄 AHK window refresh")
        return self.send_command("REFRESH")
    
    def stop(self):
        """Остановить AHK процесс"""
        if self.process and self.process.poll() is None:
            try:
                self.send_command("EXIT")
                self.process.wait(timeout=2)
                logging.info("✅ AHK stopped gracefully")
            except subprocess.TimeoutExpired:
                self.process.kill()
                logging.warning("⚠️ AHK killed forcefully")
            except Exception as e:
                logging.warning(f"⚠️ Error stopping AHK: {e}")