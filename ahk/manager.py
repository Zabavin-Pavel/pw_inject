"""
Менеджер AHK - ОБНОВЛЕНО: копирование settings.ini в AppData
"""
import subprocess
import logging
from pathlib import Path
import time
import sys
import shutil
import hashlib

class AHKManager:
    """Управление AutoHotkey скриптом"""
    
    def __init__(self):
        self.process = None
        self.appdata_dir = Path.home() / "AppData" / "Local" / "xvocmuk"
        self.appdata_dir.mkdir(parents=True, exist_ok=True)
        self.command_file = self.appdata_dir / "ahk_command.txt"
        
        # Скопировать файлы из bundle в AppData при необходимости
        self._ensure_files_in_appdata()
        
        # Запустить AHK
        self._start_ahk()
    
    def _ensure_files_in_appdata(self):
        """
        Скопировать hotkeys.exe и settings.ini из bundle в AppData
        
        - hotkeys.exe: копируется ВСЕГДА если хеш не совпадает (обновление)
        - settings.ini: копируется ТОЛЬКО если отсутствует (портативная версия)
        """
        # Определяем путь к bundle
        if getattr(sys, 'frozen', False):
            # Скомпилированный EXE
            bundle_dir = Path(sys._MEIPASS) / "ahk"
        else:
            # Dev режим
            bundle_dir = Path(__file__).parent
        
        # === HOTKEYS.EXE (с проверкой хеша) ===
        source_exe = bundle_dir / "hotkeys.exe"
        target_exe = self.appdata_dir / "hotkeys.exe"
        
        if not source_exe.exists():
            logging.error(f"❌ Source hotkeys.exe not found: {source_exe}")
            return
        
        # Проверяем хеш
        should_copy_exe = True
        
        if target_exe.exists():
            source_hash = self._compute_file_hash(source_exe)
            target_hash = self._compute_file_hash(target_exe)
            
            if source_hash == target_hash:
                should_copy_exe = False
                logging.info(f"✅ hotkeys.exe hash match, skip copy")
            else:
                logging.info(f"⚠️ hotkeys.exe hash mismatch, updating...")
        
        if should_copy_exe:
            try:
                shutil.copy2(source_exe, target_exe)
                logging.info(f"✅ hotkeys.exe copied to {target_exe}")
            except Exception as e:
                logging.error(f"❌ Failed to copy hotkeys.exe: {e}")
        
        # === SETTINGS.INI (только если отсутствует) ===
        source_ini = bundle_dir / "settings.ini"
        target_ini = self.appdata_dir / "settings.ini"
        
        if not source_ini.exists():
            logging.warning(f"⚠️ Source settings.ini not found: {source_ini}")
            return
        
        if not target_ini.exists():
            try:
                shutil.copy2(source_ini, target_ini)
                logging.info(f"✅ settings.ini copied to {target_ini}")
            except Exception as e:
                logging.error(f"❌ Failed to copy settings.ini: {e}")
        else:
            logging.info(f"ℹ️ settings.ini already exists, skip copy")
    
    def _compute_file_hash(self, filepath: Path) -> str:
        """Вычислить SHA256 хеш файла"""
        sha256 = hashlib.sha256()
        
        try:
            with open(filepath, 'rb') as f:
                while chunk := f.read(8192):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except Exception as e:
            logging.error(f"Failed to compute hash for {filepath}: {e}")
            return ""
    
    def _start_ahk(self):
        """Запустить AHK процесс"""
        try:
            # Путь к hotkeys.exe в AppData
            ahk_exe = self.appdata_dir / "hotkeys.exe"
            
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
    
    def follow_leader(self):
        """Follow - клик во всех окнах кроме лидера"""
        return self.send_command("FOLLOW")
    
    def start_headhunter(self):
        """Headhunter - Tab + клик в активном окне"""
        return self.send_command("HEADHUNTER_START")
    
    def stop_headhunter(self):
        """Headhunter - Tab + клик в активном окне"""
        return self.send_command("HEADHUNTER_STOP")
    
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