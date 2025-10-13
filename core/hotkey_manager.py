"""
Менеджер хоткеев с централизованным listener'ом
"""
import logging
import keyboard
import threading
import time

class HotkeyManager:
    """Менеджер глобальных хоткеев"""
    
    def __init__(self, action_manager, on_hotkey_executed=None):
        self.action_manager = action_manager
        self.on_hotkey_executed = on_hotkey_executed
        self.bindings = {}  # {hotkey: action_id}
        
        # Для режима записи
        self.recording_mode = False
        
        # Отслеживание всех нажатых клавиш
        self.pressed_keys = set()
        
        # === LISTENER МЕХАНИЗМ ===
        self.listener_thread = None
        self.listener_active = False
        self.listener_lock = threading.Lock()
        
        self.current_action_id = None
        self.current_hotkey = None
        self.last_trigger_time = 0
        
        # НОВОЕ: Параметры как в Windows
        self.initial_delay = 0.5        # 500ms - задержка после первого нажатия
        self.repeat_throttle = 0.1      # 100ms - быстрые повторения
        self.listener_timeout = 1.0     # 1 секунда ожидания перед закрытием
        
        # Хук для отслеживания клавиш
        keyboard.hook(self._on_key_event, suppress=False)
    
    def _on_key_event(self, event):
        """Обработка всех событий клавиш"""
        key_name = self._normalize_key_name(event.name)
        
        if event.event_type == 'down':
            self.pressed_keys.add(key_name)
            
            if not self.recording_mode:
                self._check_hotkeys(key_name)
        elif event.event_type == 'up':
            self.pressed_keys.discard(key_name)
    
    def _normalize_key_name(self, key_name: str) -> str:
        """Нормализовать имя клавиши"""
        shift_number_map = {
            '!': '1', '@': '2', '#': '3', '$': '4', '%': '5',
            '^': '6', '&': '7', '*': '8', '(': '9', ')': '0'
        }
        
        ru_to_en = {
            'й': 'q', 'ц': 'w', 'у': 'e', 'к': 'r', 'е': 't', 'н': 'y', 
            'г': 'u', 'ш': 'i', 'щ': 'o', 'з': 'p', 'х': '[', 'ъ': ']',
            'ф': 'a', 'ы': 's', 'в': 'd', 'а': 'f', 'п': 'g', 'р': 'h', 
            'о': 'j', 'л': 'k', 'д': 'l', 'ж': ';', 'э': "'",
            'я': 'z', 'ч': 'x', 'с': 'c', 'м': 'v', 'и': 'b', 
            'т': 'n', 'ь': 'm', 'б': ',', 'ю': '.'
        }
        
        key_lower = key_name.lower()
        
        if key_name in shift_number_map:
            return shift_number_map[key_name]
        
        if key_lower == 'shift':
            return 'left shift'
        elif key_lower == 'ctrl':
            return 'left ctrl'
        elif key_lower == 'alt':
            return 'left alt'
        
        if key_lower in ru_to_en:
            return ru_to_en[key_lower].upper()
        
        if len(key_name) == 1 and key_name.isalpha():
            return key_name.upper()
        
        if len(key_name) == 1 and key_name.isdigit():
            return key_name
        
        return key_name

    def _check_hotkeys(self, pressed_key: str):
        """Проверить все хоткеи при нажатии клавиши"""
        check_key = pressed_key.replace('left ', '').replace('right ', '')
        
        for hotkey, action_id in self.bindings.items():
            if self._hotkey_matches(hotkey, check_key):
                logging.info(f"Hotkey '{hotkey}' triggered for action: {action_id}")
                self._trigger_listener(action_id, hotkey)
                break

    def _hotkey_matches(self, hotkey: str, pressed_key: str) -> bool:
        """Проверить, соответствует ли текущее состояние клавиатуры хоткею"""
        parts = hotkey.split('+')
        
        main_key = None
        required_modifiers = set()
        
        for part in parts:
            part_lower = part.lower()
            if part_lower in ['shift', 'ctrl', 'alt']:
                required_modifiers.add('left ' + part_lower)
            else:
                main_key = part
        
        if main_key != pressed_key:
            return False
        
        modifier_keys = {'left shift', 'left ctrl', 'left alt', 
                        'right shift', 'right ctrl', 'right alt'}
        
        for mod_key in modifier_keys:
            is_pressed = mod_key in self.pressed_keys
            is_required = mod_key in required_modifiers
            
            if is_pressed and not is_required:
                return False
            if is_required and not is_pressed:
                return False
        
        return True

    def _trigger_listener(self, action_id: str, hotkey: str):
        """Триггер для listener'а"""
        with self.listener_lock:
            self.current_action_id = action_id
            self.current_hotkey = hotkey
            self.last_trigger_time = time.time()
            
            if not self.listener_active:
                self.listener_active = True
                self.listener_thread = threading.Thread(
                    target=self._listener_loop,
                    daemon=True
                )
                self.listener_thread.start()
                logging.info("Listener thread started")

    def _listener_loop(self):
        """
        Основной цикл listener'а с Windows-подобным поведением:
        1. Первое выполнение - сразу
        2. Пауза (initial_delay)
        3. Быстрые повторения (repeat_throttle)
        """
        first_execution = True
        after_initial_delay = False
        
        while self.listener_active:
            with self.listener_lock:
                action_id = self.current_action_id
                hotkey = self.current_hotkey
            
            if not action_id:
                time.sleep(0.05)
                continue
            
            # === ПРОВЕРКА: Если это НЕ первый вызов - проверяем нажата ли клавиша ===
            if not first_execution:
                if not self._is_hotkey_still_pressed(hotkey):
                    # Клавиша отпущена - проверяем таймаут
                    current_time = time.time()
                    time_since_last_trigger = current_time - self.last_trigger_time
                    
                    if time_since_last_trigger >= self.listener_timeout:
                        logging.info("Listener timeout - stopping")
                        with self.listener_lock:
                            self.listener_active = False
                            self.current_action_id = None
                            self.current_hotkey = None
                        break
                    else:
                        time.sleep(0.05)
                        continue
            
            # === ВЫПОЛНИТЬ ЭКШЕН ===
            try:
                self.action_manager.execute(action_id)
                
                if self.on_hotkey_executed:
                    self.on_hotkey_executed(action_id)
                
                logging.debug(f"Listener executed: {action_id}")
            except Exception as e:
                logging.error(f"Error in listener executing {action_id}: {e}")
            
            # === ЗАДЕРЖКА В СТИЛЕ WINDOWS ===
            if first_execution:
                # После первого нажатия - ДОЛГАЯ пауза (500ms)
                first_execution = False
                time.sleep(self.initial_delay)
                after_initial_delay = True
            else:
                # После initial_delay - БЫСТРЫЕ повторения (50ms)
                time.sleep(self.repeat_throttle)

    def _is_hotkey_still_pressed(self, hotkey: str) -> bool:
        """Проверить, нажата ли ещё комбинация клавиш"""
        if not hotkey:
            return False
        
        parts = hotkey.split('+')
        
        # ОТЛАДКА: Выводим что проверяем
        logging.debug(f"Checking hotkey: {hotkey}, pressed_keys: {self.pressed_keys}")
        
        for part in parts:
            part_lower = part.lower()
            
            # Проверяем модификаторы
            if part_lower == 'shift':
                if 'left shift' not in self.pressed_keys and 'right shift' not in self.pressed_keys:
                    logging.debug(f"Shift not pressed")
                    return False
            elif part_lower == 'ctrl':
                if 'left ctrl' not in self.pressed_keys and 'right ctrl' not in self.pressed_keys:
                    logging.debug(f"Ctrl not pressed")
                    return False
            elif part_lower == 'alt':
                if 'left alt' not in self.pressed_keys and 'right alt' not in self.pressed_keys:
                    logging.debug(f"Alt not pressed")
                    return False
            else:
                # Обычная клавиша
                # Проверяем в разных форматах
                found = False
                
                # 1. Как есть
                if part in self.pressed_keys:
                    found = True
                # 2. UPPERCASE (для букв)
                elif part.upper() in self.pressed_keys:
                    found = True
                # 3. lowercase (на всякий случай)
                elif part.lower() in self.pressed_keys:
                    found = True
                
                if not found:
                    logging.debug(f"Key '{part}' not found in pressed_keys")
                    return False
        
        logging.debug(f"All keys still pressed")
        return True

    def set_recording_mode(self, enabled: bool):
        """Режим записи - отключает срабатывание хоткеев"""
        self.recording_mode = enabled
    
    def bind(self, hotkey: str, action_id: str):
        """Привязать хоткей к действию"""
        old_hotkey = self._find_hotkey_by_action(action_id)
        if old_hotkey and old_hotkey != hotkey:
            self.unbind(old_hotkey)
        
        if hotkey in self.bindings:
            old_action = self.bindings[hotkey]
            if old_action != action_id:
                logging.info(f"Hotkey {hotkey} reassigned from {old_action} to {action_id}")
        
        self.bindings[hotkey] = action_id
        logging.info(f"Bound hotkey '{hotkey}' to action '{action_id}'")
    
    def unbind(self, hotkey: str):
        """Отвязать хоткей"""
        if hotkey in self.bindings:
            action_id = self.bindings.pop(hotkey)
            logging.info(f"Unbound hotkey '{hotkey}' from action '{action_id}'")
    
    def unbind_all(self):
        """Отвязать все хоткеи"""
        self.bindings.clear()
        logging.info("All hotkeys unbound")
    
    def get_hotkey_for_action(self, action_id: str) -> str:
        """Получить хоткей для действия"""
        for hotkey, aid in self.bindings.items():
            if aid == action_id:
                return hotkey
        return ""
    
    def _find_hotkey_by_action(self, action_id: str) -> str:
        """Найти хоткей по ID действия"""
        for hotkey, aid in self.bindings.items():
            if aid == action_id:
                return hotkey
        return None
    
    def stop(self):
        """Остановить менеджер"""
        with self.listener_lock:
            self.listener_active = False
        
        if self.listener_thread and self.listener_thread.is_alive():
            self.listener_thread.join(timeout=2)
        
        self.unbind_all()
        try:
            keyboard.unhook_all()
        except:
            pass
        logging.info("Hotkey manager stopped")