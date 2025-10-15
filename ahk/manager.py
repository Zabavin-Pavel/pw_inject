"""
Менеджер AHK - запускает и управляет hotkeys.exe
ОБНОВЛЕНО: Автообновление hotkeys.exe по хеш-сумме
"""
import subprocess
import sys
import time
import atexit
import logging
import hashlib
from pathlib import Path
import shutil

class AHKManager:
    """Управляет постоянным AHK процессом"""
    
    def __init__(self):
        # AppData папка (постоянное хранилище)
        self.appdata_dir = Path.home() / "AppData" / "Local" / "xvocmuk"
        self.appdata_dir.mkdir(parents=True, exist_ok=True)
        
        # Определяем пути в зависимости от режима запуска
        if getattr(sys, 'frozen', False):
            # === УПАКОВАН В EXE ===
            temp_dir = Path(sys._MEIPASS)
            bundled_ahk = temp_dir / "ahk" / "hotkeys.exe"
            
            if not bundled_ahk.exists():
                logging.error(f"❌ Bundled hotkeys.exe not found at {bundled_ahk}")
                bundled_ahk = None
        else:
            # === РАЗРАБОТКА (из исходников) ===
            base_path = Path(__file__).parent.parent
            bundled_ahk = base_path / "ahk" / "hotkeys.exe"
            
            if not bundled_ahk.exists():
                logging.warning(f"⚠️ hotkeys.exe not found at {bundled_ahk}")
                bundled_ahk = None
        
        # hotkeys.exe в AppData (для выполнения)
        self.ahk_exe = self.appdata_dir / "hotkeys.exe"
        
        # ahk_command.txt в AppData (writable)
        self.command_file = self.appdata_dir / "ahk_command.txt"
        
        # === АВТООБНОВЛЕНИЕ ПО ХЕШУ ===
        if bundled_ahk:
            self._update_hotkeys_if_needed(bundled_ahk)
        
        self.process = None
        
        # Запускаем AHK при создании
        self.start()
        
        # Регистрируем остановку при выходе
        atexit.register(self.stop)
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Вычислить SHA256 хеш файла"""
        sha256 = hashlib.sha256()
        
        try:
            with open(file_path, 'rb') as f:
                # Читаем файл блоками для экономии памяти
                while chunk := f.read(8192):
                    sha256.update(chunk)
            
            return sha256.hexdigest()
        except Exception as e:
            logging.error(f"❌ Failed to calculate hash for {file_path}: {e}")
            return ""
    
    def _update_hotkeys_if_needed(self, bundled_ahk: Path):
        """
        Обновить hotkeys.exe в AppData если хеш отличается
        
        Логика:
        1. Если файл в AppData не существует - копируем
        2. Если хеши отличаются - перезаписываем
        3. Если хеши одинаковые - ничего не делаем
        """
        # Вычисляем хеш bundled версии
        bundled_hash = self._calculate_file_hash(bundled_ahk)
        
        if not bundled_hash:
            logging.error("❌ Cannot calculate bundled hotkeys.exe hash")
            return
        
        # Проверяем существует ли файл в AppData
        if not self.ahk_exe.exists():
            # Файл отсутствует - копируем
            try:
                shutil.copy(bundled_ahk, self.ahk_exe)
                logging.info(f"✅ Installed hotkeys.exe to {self.ahk_exe}")
                logging.info(f"   Hash: {bundled_hash[:16]}...")
            except Exception as e:
                logging.error(f"❌ Failed to install hotkeys.exe: {e}")
            return
        
        # Файл существует - проверяем хеш
        appdata_hash = self._calculate_file_hash(self.ahk_exe)
        
        if bundled_hash != appdata_hash:
            # Хеши отличаются - обновляем
            try:
                # Останавливаем старый процесс если запущен
                if self.process and self.process.poll() is None:
                    try:
                        self.process.kill()
                        self.process.wait(timeout=1)
                    except:
                        pass
                
                # Копируем новую версию
                shutil.copy(bundled_ahk, self.ahk_exe)
                logging.info(f"🔄 Updated hotkeys.exe in {self.ahk_exe}")
                logging.info(f"   Old hash: {appdata_hash[:16]}...")
                logging.info(f"   New hash: {bundled_hash[:16]}...")
            except Exception as e:
                logging.error(f"❌ Failed to update hotkeys.exe: {e}")
        else:
            # Хеши совпадают - обновление не требуется
            logging.info(f"✅ hotkeys.exe is up to date")
            logging.info(f"   Hash: {bundled_hash[:16]}...")
    
    def start(self):
        """Запустить AHK процесс"""
        if not self.ahk_exe.exists():
            logging.error(f"❌ AHK not found: {self.ahk_exe}")
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
            logging.info(f"✅ AHK started (PID: {self.process.pid})")
            logging.info(f"📝 Command file: {self.command_file}")
            
            # Даём AHK время на инициализацию
            time.sleep(0.5)
            
            return True
        except Exception as e:
            logging.error(f"❌ Failed to start AHK: {e}")
            return False
    
    def send_command(self, command: str):
        """Отправить команду в AHK"""
        if not self.process or self.process.poll() is not None:
            logging.warning("⚠️ AHK not running, restarting...")
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
            logging.error(f"❌ Failed to send command: {e}")
            return False
    
    def click_at_mouse(self):
        """Кликнуть во всех окнах в текущей позиции мыши"""
        return self.send_command("CLICK")
    
    def send_key(self, key: str):
        """Отправить клавишу во все окна"""
        return self.send_command(f"KEY:{key}")

    def send_key_to_pid(self, key: str, pid: int):
        """Отправить клавишу конкретному окну по PID"""
        return self.send_command(f"KEY_PID:{key}:{pid}")
    
    def headhunter(self, pid: int):
        """Выполнить Headhunter для конкретного окна по PID"""
        return self.send_command(f"HEADHUNTER:{pid}")
    
    def follow_lider(self):
        """Выполнить Follow Lider для всех окон"""
        return self.send_command("FOLLOW_LIDER")
    
    def refresh_windows(self):
        """Обновить список окон в AHK"""
        logging.info("🔄 Refreshing AHK window list")
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