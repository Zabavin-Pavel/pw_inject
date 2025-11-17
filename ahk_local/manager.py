"""
AHK Manager v3 - Python AHK API
"""
import logging
import configparser
import time  # ← ДОБАВЬ
from pathlib import Path
from typing import List, Optional
from ahk import AHK
from ahk.directives import NoTrayIcon
import sys


class AHKManager:
    """Управление окнами через Python AHK API"""
    
    def __init__(self):
        """Инициализация менеджера"""
        # НОВОЕ: Определяем путь к AutoHotkey.exe
        if getattr(sys, 'frozen', False):
            # Режим EXE - AutoHotkey.exe упакован в _internal
            ahk_path = Path(sys._MEIPASS) / 'AutoHotkey.exe'
            
            if not ahk_path.exists():
                raise FileNotFoundError(
                    f"AutoHotkey.exe not found at {ahk_path}. "
                    "Please rebuild with: pyinstaller build.spec --clean"
                )
            
            logging.info(f"📍 AHK executable: {ahk_path}")
        else:
            # Режим разработки - используем из venv (AHK найдёт сам)
            ahk_path = None
        
        # Инициализируем AHK с явным путём (если EXE)
        self.ahk = AHK(
            executable_path=str(ahk_path) if ahk_path else None,
            directives=[NoTrayIcon(apply_to_hotkeys_process=True)],
            version='v1'
        )
        
        # Загружаем координаты
        self.coords = self._load_coordinates()
        
        # Кеш окон
        self.windows = []
        self.pid_to_hwnd = {}
        
        self.refresh_windows()
        
        logging.info("✅ AHK Manager initialized")
    
    def _load_coordinates(self) -> dict:
        """Загрузить координаты из settings.ini"""
        appdata_dir = Path.home() / "AppData" / "Local" / "xvocmuk"
        settings_file = appdata_dir / "settings.ini"
        
        if not settings_file.exists():
            appdata_dir.mkdir(parents=True, exist_ok=True)
            self._create_default_settings(settings_file)
        
        config = configparser.ConfigParser()
        config.read(settings_file, encoding='utf-8')
        
        coords = {}
        if config.has_section('Coordinates'):
            for key, value in config.items('Coordinates'):
                coords[key] = int(value)
        
        return coords
    
    def _create_default_settings(self, settings_file: Path):
        """Создать дефолтный settings.ini"""
        config = configparser.ConfigParser()
        config['Coordinates'] = {
            'static_x': '115',
            'static_y': '75',
            'headhunter_x': '405',
            'headhunter_y': '554',
            'leader_x': '411',
            'leader_y': '666',
            'macros_spam_x': '1300',
            'macros_spam_y': '850',
            'macro_boss_x': '1350',
            'macro_boss_y': '850'
        }
        
        with open(settings_file, 'w', encoding='utf-8') as f:
            config.write(f)
    
    def refresh_windows(self):
        """Обновить список окон и кеш PID→HWND"""
        self.windows = self.ahk.find_windows(title='Asgard Perfect World')
        self.pid_to_hwnd.clear()
        
        for window in self.windows:
            try:
                pid = window.get_pid()
                hwnd = window.id
                self.pid_to_hwnd[pid] = hwnd
                logging.debug(f"   Cached: PID={pid} → HWND={hwnd}")
            except Exception as e:
                logging.error(f"   Failed to cache window: {e}")
                continue
        
        logging.info(f"🔄 Found {len(self.windows)} windows, cached {len(self.pid_to_hwnd)} PIDs")
    
    def _get_windows_by_pids(self, target_pids: List[int]):
        """Получить Window объекты по списку PIDs"""
        logging.info(f"🔍 Getting windows for PIDs: {target_pids}")
        logging.info(f"   Cache has: {list(self.pid_to_hwnd.keys())}")
        
        filtered = []
        
        for window in self.windows:
            try:
                pid = window.get_pid()
                
                if pid in target_pids:
                    filtered.append(window)
                    logging.info(f"   ✓ Found: PID={pid}, HWND={window.id}")
            except Exception as e:
                logging.error(f"   ✗ Failed to get PID: {e}")
                continue
        
        logging.info(f"✅ Filtered: {len(filtered)}/{len(target_pids)} windows")
        return filtered
    
    def click_at_mouse(self, target_pids: Optional[List[int]] = None) -> bool:
        """Клик ЛКМ по позиции курсора"""
        try:
            self.refresh_windows()
            
            mouse_pos = self.ahk.get_mouse_position()
            x, y = mouse_pos
            
            if target_pids:
                windows = self._get_windows_by_pids(target_pids)
            else:
                windows = self.windows
            
            for window in windows:
                window.click(x=x, y=y, button='L')
            
            return True
        except Exception as e:
            logging.error(f"❌ click_at_mouse failed: {e}")
            return False
    
    def send_key(self, key: str = 'space', target_pids: Optional[List[int]] = None) -> bool:
        """Отправить клавишу"""
        try:
            if not target_pids:
                return False
            
            self.refresh_windows()
            
            windows = self._get_windows_by_pids(target_pids)
            
            for window in windows:
                window.click(x=115, y=75, button='L')
                window.send(f'{{{key}}}')
            
            return True
        except Exception as e:
            logging.error(f"❌ send_key failed: {e}")
            return False
    
    def follow_leader(self, target_pids: Optional[List[int]] = None) -> bool:
        """Follow Leader (ПКМ→Ассист→ПКМ→Follow)"""
        logging.info(f"👣 follow_leader called with target_pids={target_pids}")
        
        try:
            if not target_pids:
                logging.warning("⚠️ No target PIDs!")
                return False
            
            self.refresh_windows()
            
            windows = self._get_windows_by_pids(target_pids)
            
            if not windows:
                logging.warning("⚠️ No windows after filtering!")
                return False
            
            logging.info(f"✅ Will execute follow for {len(windows)} windows")
            
            leader_x = self.coords.get('leader_x', 411)
            leader_y = self.coords.get('leader_y', 666)
            offset_x = leader_x + 30
            assist_y = leader_y + 65
            follow_y = leader_y + 50
            
            for window in windows:
                # window.click(x=115, y=75, button='L')
                pid = window.get_pid()
                logging.info(f"   Executing follow for PID={pid}, HWND={window.id}")
                window.click(x=leader_x, y=leader_y, button='R')
                window.click(x=offset_x, y=assist_y, button='L')
                window.click(x=leader_x, y=leader_y, button='R')
                window.click(x=offset_x, y=follow_y, button='L')
            
            logging.info("✅ Follow sequence completed!")
            return True
        except Exception as e:
            logging.error(f"❌ follow_leader failed: {e}", exc_info=True)
            return False
    
    def stop(self):
        """Остановить менеджер"""
        self.pid_to_hwnd.clear()
        self.windows.clear()
        logging.info("🛑 AHK Manager stopped")
    
    def cleanup(self):
        """Очистка ресурсов"""
        self.stop()