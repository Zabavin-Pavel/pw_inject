"""
AHK Manager v2 - работа через командную строку без файлов
"""
import subprocess
import logging
from pathlib import Path
import sys
import hashlib
from typing import Optional, List

class AHKManager:
    """Управление AutoHotkey через прямые вызовы команд"""
    
    def __init__(self):
        """Инициализация менеджера"""
        self.appdata_dir = Path.home() / "AppData" / "Local" / "xvocmuk"
        self.appdata_dir.mkdir(parents=True, exist_ok=True)
        
        # Путь к исполняемому AHK скрипту
        self.ahk_exe = self.appdata_dir / "hotkeys.exe"
        
        # Координаты UI (загружаются из конфига)
        self.leader_x = 411
        self.leader_y = 666
        self.headhunter_x = 394
        self.headhunter_y = 553
        self.macros_spam_x = 0
        self.macros_spam_y = 0
        
        # Копирование AHK exe в AppData
        self._ensure_ahk_in_appdata()
    
    def _ensure_ahk_in_appdata(self):
        """Копирование hotkeys.exe в AppData с проверкой хеша"""
        if getattr(sys, 'frozen', False):
            bundle_dir = Path(sys._MEIPASS) / "ahk"
        else:
            bundle_dir = Path(__file__).parent
        
        source_exe = bundle_dir / "hotkeys.exe"
        
        if not source_exe.exists():
            logging.error(f"❌ Source AHK exe not found: {source_exe}")
            return
        
        # Проверка хеша и копирование
        should_copy = True
        
        if self.ahk_exe.exists():
            source_hash = self._compute_file_hash(source_exe)
            target_hash = self._compute_file_hash(self.ahk_exe)
            
            if source_hash == target_hash:
                should_copy = False
                logging.info("✅ AHK exe актуален")
            else:
                logging.info("⚠️ Обновление AHK exe...")
        
        if should_copy:
            import shutil
            shutil.copy2(source_exe, self.ahk_exe)
            logging.info(f"✅ AHK exe скопирован: {self.ahk_exe}")
    
    def _compute_file_hash(self, filepath: Path) -> str:
        """Вычислить SHA256 хеш файла"""
        sha256 = hashlib.sha256()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def _execute_command(self, args: List[str]) -> bool:
        """
        Выполнить AHK команду
        
        Args:
            args: список аргументов для AHK exe
        
        Returns:
            bool: успешность выполнения
        """
        try:
            if not self.ahk_exe.exists():
                logging.error(f"❌ AHK exe not found: {self.ahk_exe}")
                return False
            
            # Формируем полную команду
            cmd = [str(self.ahk_exe)] + args
            
            # Запускаем процесс без окна
            subprocess.Popen(
                cmd,
                creationflags=subprocess.CREATE_NO_WINDOW,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            return True
            
        except Exception as e:
            logging.error(f"❌ Failed to execute AHK command {args}: {e}")
            return False
    
    def _get_excluded_pids_string(self, excluded_pids: Optional[List[int]] = None) -> str:
        """
        Конвертировать список PIDs в строку для AHK
        
        Args:
            excluded_pids: список PIDs для исключения
        
        Returns:
            str: PIDs через запятую или пустая строка
        """
        if not excluded_pids:
            return ""
        
        return ",".join(str(pid) for pid in excluded_pids)
    
    # === КОНФИГУРАЦИЯ ===
    
    def update_coordinates(self, 
                          leader_x: Optional[int] = None,
                          leader_y: Optional[int] = None,
                          headhunter_x: Optional[int] = None,
                          headhunter_y: Optional[int] = None,
                          macros_spam_x: Optional[int] = None,
                          macros_spam_y: Optional[int] = None):
        """
        Обновить координаты UI
        
        Args:
            leader_x: X координата меню лидера
            leader_y: Y координата меню лидера
            headhunter_x: X координата кнопки headhunter
            headhunter_y: Y координата кнопки headhunter
            macros_spam_x: X координата кнопки макроса
            macros_spam_y: Y координата кнопки макроса
        """
        if leader_x is not None:
            self.leader_x = leader_x
        if leader_y is not None:
            self.leader_y = leader_y
        if headhunter_x is not None:
            self.headhunter_x = headhunter_x
        if headhunter_y is not None:
            self.headhunter_y = headhunter_y
        if macros_spam_x is not None:
            self.macros_spam_x = macros_spam_x
        if macros_spam_y is not None:
            self.macros_spam_y = macros_spam_y
        
        # Отправить команду в AHK для обновления координат
        args = [
            "coords",
            str(self.leader_x),
            str(self.leader_y),
            str(self.headhunter_x),
            str(self.headhunter_y),
            str(self.macros_spam_x),
            str(self.macros_spam_y)
        ]
        
        return self._execute_command(args)
    
    # === ОСНОВНЫЕ КОМАНДЫ ===
    
    def click_at_mouse(self, excluded_pids: Optional[List[int]] = None) -> bool:
        """
        Кликнуть по текущей позиции мыши во всех окнах
        
        Args:
            excluded_pids: список PIDs окон для исключения
        
        Returns:
            bool: успешность выполнения
        """
        excluded_str = self._get_excluded_pids_string(excluded_pids)
        args = ["click", excluded_str] if excluded_str else ["click"]
        
        return self._execute_command(args)
    
    def follow_leader(self, target_pids: Optional[List[int]] = None) -> bool:
        """
        Следовать за лидером в указанных окнах
        
        Args:
            target_pids: список PIDs окон для выполнения команды
        
        Returns:
            bool: успешность выполнения
        """
        if not target_pids:
            logging.warning("⚠️ No target_pids provided for follow_leader")
            return False
        
        target_str = ",".join(str(pid) for pid in target_pids)
        args = ["follow", target_str]
        
        return self._execute_command(args)
    
    def attack_guard(self, excluded_pids: Optional[List[int]] = None) -> bool:
        """
        Атаковать цель лидера с использованием Guard макроса
        
        Args:
            excluded_pids: список PIDs окон для исключения
        
        Returns:
            bool: успешность выполнения
        """
        excluded_str = self._get_excluded_pids_string(excluded_pids)
        args = ["attack_guard", excluded_str] if excluded_str else ["attack_guard"]
        
        return self._execute_command(args)
    
    def send_key(self, 
                 key: str, 
                 window_ids: Optional[List[int]] = None,
                 repeat_count: int = 1) -> bool:
        """
        Отправить клавишу в конкретные окна
        
        Args:
            key: клавиша для отправки (например, "space", "f", "1")
            window_ids: список Window IDs окон для отправки
            repeat_count: количество повторов нажатия
        
        Returns:
            bool: успешность выполнения
        """
        if not window_ids:
            logging.warning("⚠️ No window_ids provided for send_key")
            return False
        
        window_ids_str = ",".join(str(wid) for wid in window_ids)
        args = ["key", key, window_ids_str]
        
        if repeat_count > 1:
            args.append(str(repeat_count))
        
        return self._execute_command(args)
    
    def headhunter_start(self, excluded_pids: Optional[List[int]] = None) -> bool:
        """
        Запустить headhunter в активном окне
        
        Args:
            excluded_pids: список PIDs окон для исключения
        
        Returns:
            bool: успешность выполнения
        """
        excluded_str = self._get_excluded_pids_string(excluded_pids)
        args = ["headhunter", excluded_str] if excluded_str else ["headhunter"]
        
        return self._execute_command(args)
    
    # === СОВМЕСТИМОСТЬ ===
    
    def refresh_windows(self):
        """
        Обновить список окон (заглушка для совместимости)
        
        В новой версии не нужно - каждая команда получает актуальный список окон
        """
        pass
    
    # === УТИЛИТЫ ===
    
    def cleanup(self):
        """Очистка ресурсов (если необходимо)"""
        # В новой версии нет постоянно запущенного процесса
        pass
    
    def __del__(self):
        """Деструктор"""
        self.cleanup()