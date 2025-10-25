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
        key_name = self._normalize_key_name(event.name)  # БЕЗ scan_code
        
        if event.event_type == 'down':
            self.pressed_keys.add(key_name)
            
            if not self.recording_mode:
                self._check_hotkeys(key_name)
        elif event.event_type == 'up':
            self.pressed_keys.discard(key_name)
    
    def _normalize_key_name(self, key_name: str) -> str:
        """Нормализовать имя клавиши"""
        
        # РАСШИРЕННЫЙ shift_number_map - все возможные раскладки
        shift_number_map = {
            # Английская раскладка
            '!': '1', '@': '2', '#': '3', '$': '4', '%': '5',
            '^': '6', '&': '7', '*': '8', '(': '9', ')': '0',
            # Русская раскладка
            '№': '3', ';': '4', ':': '6', '?': '7',
            # Дополнительно (на всякий случай)
            '"': '2',
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
        
        # Символы Shift+цифра -> цифра (ПЕРВЫМ!)
        if key_name in shift_number_map:
            return shift_number_map[key_name]
        
        # Модификаторы
        if key_lower == 'shift':
            return 'left shift'
        elif key_lower == 'ctrl':
            return 'left ctrl'
        elif key_lower == 'alt':
            return 'left alt'
        
        # Русские буквы -> английские (UPPERCASE)
        if key_lower in ru_to_en:
            return ru_to_en[key_lower].upper()
        
        # Буквы - UPPERCASE
        if len(key_name) == 1 and key_name.isalpha():
            return key_name.upper()
        
        # Цифры
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
            # ИСПРАВЛЕНО: Если listener уже активен для ЭТОГО ЖЕ экшена
            if self.listener_active and self.current_action_id == action_id:
                # Просто обновляем время последнего триггера
                # Это позволит продолжить работу без создания нового треда
                self.last_trigger_time = time.time()
                logging.debug(f"Re-triggered active listener for {action_id}")
                return
            
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
        3. Быстрые повторения (repeat_throttle) ТОЛЬКО ЕСЛИ ХОТКЕЙ НАЖАТ
        """
        first_execution = True
        last_execution_time = 0
        
        while self.listener_active:
            with self.listener_lock:
                action_id = self.current_action_id
                hotkey = self.current_hotkey
            
            if not action_id:
                time.sleep(0.05)
                continue
            
            current_time = time.time()
            
            # === ПРОВЕРКА: ХОТКЕЙ НАЖАТ? ===
            hotkey_pressed = self._is_hotkey_still_pressed(hotkey)
            
            # ИСПРАВЛЕНО: Выполняем ТОЛЬКО если хоткей нажат (или это первый раз)
            should_execute = False
            wait_time = 0.05  # По умолчанию короткая пауза
            
            if first_execution:
                # Первый раз - выполняем всегда
                should_execute = True
                wait_time = self.initial_delay  # После первого - долгая пауза
                first_execution = False
                last_execution_time = current_time
            elif hotkey_pressed:
                # Хоткей нажат - проверяем прошло ли достаточно времени
                time_since_last_exec = current_time - last_execution_time
                
                if time_since_last_exec >= self.repeat_throttle:
                    should_execute = True
                    wait_time = self.repeat_throttle  # Быстрые повторения
                    last_execution_time = current_time
            
            # === ВЫПОЛНИТЬ ЭКШЕН (если нужно) ===
            if should_execute:
                # === ПРОВЕРКА: АКТИВНО ЛИ ОКНО ElementClient? ===
                if not self._is_elementclient_active():
                    time.sleep(wait_time)
                    continue
                
                try:
                    self.action_manager.execute(action_id)
                    
                    if self.on_hotkey_executed:
                        self.on_hotkey_executed(action_id)
                    
                    logging.debug(f"Listener executed: {action_id}")
                except Exception as e:
                    logging.error(f"Error in listener executing {action_id}: {e}")
            
            # === ПРОВЕРКА ТАЙМАУТА ===
            if not hotkey_pressed:
                # Хоткей отпущен - проверяем таймаут
                time_since_last_trigger = current_time - self.last_trigger_time
                
                if time_since_last_trigger >= self.listener_timeout:
                    logging.info("Listener timeout - stopping")
                    with self.listener_lock:
                        self.listener_active = False
                        self.current_action_id = None
                        self.current_hotkey = None
                    break
                wait_time = 0.05  # Короткая пауза в режиме ожидания
            
            # Пауза перед следующей итерацией
            time.sleep(wait_time)

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

    def _is_elementclient_active(self) -> bool:
        """
        Проверить, является ли активное окно ElementClient.exe
        
        Returns:
            bool: True если активно окно ElementClient
        """
        try:
            import ctypes
            from ctypes import wintypes
            
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32
            
            # Получаем HWND активного окна
            hwnd = user32.GetForegroundWindow()
            
            if not hwnd:
                return False
            
            # Получаем PID процесса
            process_id = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id))
            
            # Открываем процесс
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            hProcess = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, process_id.value)
            
            if not hProcess:
                return False
            
            try:
                # Получаем имя процесса
                MAX_PATH = 260
                exe_name = ctypes.create_unicode_buffer(MAX_PATH)
                size = wintypes.DWORD(MAX_PATH)
                
                if kernel32.QueryFullProcessImageNameW(hProcess, 0, exe_name, ctypes.byref(size)):
                    full_path = exe_name.value
                    process_name = full_path.split('\\')[-1].lower()
                    
                    return process_name == 'elementclient.exe'
                
            finally:
                kernel32.CloseHandle(hProcess)
            
            return False
            
        except Exception as e:
            logging.error(f"Error checking active window: {e}")
            return False