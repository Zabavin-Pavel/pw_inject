"""
AHK Manager - управление AutoHotkey скриптом
ОБНОВЛЕНО: все функции принимают PID в аргументах
"""
import subprocess
import logging
import time
from pathlib import Path
import shutil
import sys

class AHKManager:
    """Управление AHK процессом и командами"""
    
    def __init__(self):
        self.process = None
        self.command_file = None
        self.ahk_exe = None
        
        # Определяем путь к hotkeys.exe
        self._setup_ahk_paths()
        
        # Запускаем AHK
        self.start()
    
    def _setup_ahk_paths(self):
        """Настроить пути к AHK файлам"""
        # AppData папка для команд
        appdata_dir = Path.home() / "AppData" / "Local" / "xvocmuk"
        appdata_dir.mkdir(parents=True, exist_ok=True)
        
        self.command_file = appdata_dir / "ahk_command.txt"
        
        if getattr(sys, 'frozen', False):
            # Prod режим - hotkeys.exe должен быть скопирован в AppData при первом запуске
            self.ahk_exe = appdata_dir / "hotkeys.exe"
            
            # Проверяем есть ли hotkeys.exe в AppData
            if not self.ahk_exe.exists():
                # Копируем из _internal/ahk/
                source = Path(sys._MEIPASS) / "ahk" / "hotkeys.exe"
                if source.exists():
                    shutil.copy2(source, self.ahk_exe)
                    logging.info(f"✅ hotkeys.exe скопирован в {self.ahk_exe}")
                else:
                    logging.error(f"❌ hotkeys.exe не найден в {source}")
        else:
            # Dev режим - используем скомпилированный hotkeys.exe из ahk/
            self.ahk_exe = Path(__file__).parent / "hotkeys.exe"
        
        logging.info(f"📁 AHK exe: {self.ahk_exe}")
        logging.info(f"📁 Command file: {self.command_file}")
    
    def start(self):
        """Запустить AHK процесс"""
        if not self.ahk_exe or not self.ahk_exe.exists():
            logging.error(f"❌ AHK executable not found: {self.ahk_exe}")
            return False
        
        try:
            # Удаляем старый файл команд
            if self.command_file.exists():
                self.command_file.unlink()
            
            # Запускаем AHK с аргументом command_file
            self.process = subprocess.Popen(
                [str(self.ahk_exe), str(self.command_file)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            logging.info(f"✅ AHK started (PID: {self.process.pid})")
            return True
            
        except Exception as e:
            logging.error(f"❌ Failed to start AHK: {e}")
            return False
    
    def send_command(self, command: str):
        """
        Отправить команду AHK скрипту
        
        Args:
            command: строка команды
        
        Returns:
            bool: успех операции
        """
        if not self.process or self.process.poll() is not None:
            logging.warning("⚠️ AHK process not running, restarting...")
            self.start()
            time.sleep(0.1)
        
        try:
            # Записываем команду в файл
            self.command_file.write_text(command, encoding='utf-8')
            
            # Небольшая задержка
            time.sleep(0.05)
            
            return True
        except Exception as e:
            logging.error(f"❌ Failed to send command: {e}")
            return False
    
    def click_at_mouse(self):
        """Кликнуть во всех окнах в текущей позиции мыши"""
        return self.send_command("CLICK")
    
    def send_key(self, key: str):
        """Отправить клавишу во все окна"""
        return self.send_command(f"KEY:{key}")

    def send_key_to_pid(self, key: str, pid: int):
        """
        Отправить клавишу конкретному окну по PID
        
        Args:
            key: клавиша для отправки
            pid: PID окна
        """
        return self.send_command(f"KEY:{key}:{pid}")
    
    def send_key_to_pids(self, key: str, pids: list):
        """
        Отправить клавишу нескольким окнам
        
        Args:
            key: клавиша для отправки
            pids: список PID
        """
        pids_str = ",".join(str(p) for p in pids)
        return self.send_command(f"KEY:{key}:{pids_str}")
    
    def headhunter(self, pid: int):
        """
        Выполнить Headhunter для конкретного окна по PID
        
        Args:
            pid: PID окна
        """
        return self.send_command(f"HEADHUNTER:{pid}")
    
    def follow_lider(self, pids: list):
        """
        Выполнить Follow Lider для списка окон
        
        Args:
            pids: список PID
        """
        pids_str = ",".join(str(p) for p in pids)
        return self.send_command(f"FOLLOW_LIDER:{pids_str}")
    
    def refresh_windows(self):
        """Обновить список окон в AHK (устарело, но оставлено для совместимости)"""
        logging.info("🔄 AHK window refresh (no-op)")
        return True
    
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