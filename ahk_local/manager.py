"""
AHK Manager v3 - Python AHK API
"""
import logging
import configparser
from pathlib import Path
from typing import List, Optional
from ahk import AHK
from ahk.directives import NoTrayIcon


class AHKManager:
    """Управление окнами через Python AHK API"""
    
    def __init__(self):
        """Инициализация менеджера"""
        # Инициализируем AHK
        self.ahk = AHK(
            directives=[NoTrayIcon(apply_to_hotkeys_process=True)],
            version='v1'
        )
        
        # Загружаем координаты
        self.coords = self._load_coordinates()
        
        # Кеш окон
        self.windows = []
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
        """Обновить список окон"""
        self.windows = self.ahk.find_windows(title='Asgard Perfect World')
        logging.info(f"🔄 Found {len(self.windows)} windows")
    
    def _filter_windows_by_pids(self, target_pids: List[int]):
        """Отфильтровать окна по PIDs"""
        logging.info(f"🔍 Filtering windows: target_pids={target_pids}")
        logging.info(f"🔍 Total windows available: {len(self.windows)}")
        
        filtered = []
        for window in self.windows:
            try:
                window_pid = window.process_id
                logging.info(f"   Window PID: {window_pid}, in target: {window_pid in target_pids}")
                
                if window_pid in target_pids:
                    filtered.append(window)
            except Exception as e:
                logging.error(f"   Failed to get PID: {e}")
                continue
        
        logging.info(f"✅ Filtered: {len(filtered)} windows")
        return filtered
    
    def click_at_mouse(self, target_pids: Optional[List[int]] = None) -> bool:
        """Клик ЛКМ по позиции курсора"""
        try:
            mouse_pos = self.ahk.get_mouse_position()
            x, y = mouse_pos
            
            windows_to_click = self._filter_windows_by_pids(target_pids) if target_pids else self.windows
            
            for window in windows_to_click:
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
            
            windows_to_send = self._filter_windows_by_pids(target_pids)
            
            for window in windows_to_send:
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
            
            windows_to_follow = self._filter_windows_by_pids(target_pids)
            
            if not windows_to_follow:
                logging.warning("⚠️ No windows after filtering!")
                return False
            
            logging.info(f"✅ Will execute follow for {len(windows_to_follow)} windows")
            
            leader_x = self.coords.get('leader_x', 411)
            leader_y = self.coords.get('leader_y', 666)
            offset_x = leader_x + 30
            assist_y = leader_y + 65
            follow_y = leader_y + 50
            
            for window in windows_to_follow:
                logging.info(f"   Executing follow sequence for window PID={window.process_id}")
                window.click(x=leader_x, y=leader_y, button='R')
                self.ahk.sleep(50)
                window.click(x=offset_x, y=assist_y, button='L')
                self.ahk.sleep(50)
                window.click(x=leader_x, y=leader_y, button='R')
                self.ahk.sleep(50)
                window.click(x=offset_x, y=follow_y, button='L')
            
            logging.info("✅ Follow sequence completed!")
            return True
        except Exception as e:
            logging.error(f"❌ follow_leader failed: {e}", exc_info=True)
            return False
        
    def cleanup(self):
        """Очистка ресурсов"""
        pass