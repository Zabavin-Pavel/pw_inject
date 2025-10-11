"""
Менеджер хоткеев с использованием библиотеки keyboard
Исправленная версия с поддержкой Left модификаторов
"""
import logging
import keyboard
import threading

class HotkeyManager:
    """Менеджер глобальных хоткеев"""
    
    def __init__(self, action_manager):
        self.action_manager = action_manager
        self.bindings = {}  # {hotkey: action_id}
        
        # Для режима записи
        self.recording_mode = False
        
        # Отслеживание всех нажатых клавиш
        self.pressed_keys = set()
        
        # Хук для отслеживания клавиш
        keyboard.hook(self._on_key_event, suppress=False)
    
    def _setup_modifier_tracking(self):
        """Настроить отслеживание модификаторов"""
        # Текущие модификаторы (только левые)
        self.modifiers = {
            'left shift': False,
            'left ctrl': False,
            'left alt': False
        }
        
        # Подписаться на события клавиш
        keyboard.hook(self._on_key_event, suppress=False)
    
    def _on_key_event(self, event):
        """Обработка всех событий клавиш"""
        key_name = event.name.lower()
        
        # Нормализовать модификаторы в формат "left modifier"
        if key_name == 'shift':
            key_name = 'left shift'
        elif key_name == 'ctrl':
            key_name = 'left ctrl'
        elif key_name == 'alt':
            key_name = 'left alt'
        # Буквы и цифры - в ВЕРХНИЙ регистр (как в GUI)
        elif len(key_name) == 1 and key_name.isalnum():
            key_name = key_name.upper()
        
        if event.event_type == 'down':
            self.pressed_keys.add(key_name)
            
            # При нажатии клавиши проверяем все хоткеи
            if not self.recording_mode:
                self._check_hotkeys(key_name)
        elif event.event_type == 'up':
            self.pressed_keys.discard(key_name)
    
    def _normalize_key_name(self, key_name: str) -> str:
        """
        Нормализовать имя клавиши
        Преобразует спецсимволы обратно в цифры/буквы
        """
        # Маппинг символов Shift+цифра -> цифра
        shift_number_map = {
            '!': '1', '@': '2', '#': '3', '$': '4', '%': '5',
            '^': '6', '&': '7', '*': '8', '(': '9', ')': '0'
        }
        
        key_lower = key_name.lower()
        
        # Если это символ от Shift+цифра - вернуть цифру
        if key_name in shift_number_map:
            return shift_number_map[key_name]
        
        # Буквы - в нижний регистр
        if len(key_name) == 1 and key_name.isalpha():
            return key_lower
        
        # Модификаторы
        if key_lower in ['shift', 'ctrl', 'alt', 'left shift', 'left ctrl', 'left alt']:
            return key_lower
        
        # Остальное как есть
        return key_lower

    def _check_hotkeys(self, pressed_key: str):
        """Проверить все хоткеи при нажатии клавиши"""
        # Убрать "left " из имени для проверки основной клавиши
        check_key = pressed_key.replace('left ', '').replace('right ', '')
        
        for hotkey, action_id in self.bindings.items():
            if self._hotkey_matches(hotkey, check_key):
                logging.info(f"Hotkey '{hotkey}' triggered for action: {action_id}")
                try:
                    self.action_manager.execute(action_id)
                except Exception as e:
                    logging.error(f"Error executing action {action_id}: {e}")
                break  # Только один хоткей за раз

    def _hotkey_matches(self, hotkey: str, pressed_key: str) -> bool:
        """
        Проверить, соответствует ли текущее состояние клавиатуры хоткею
        """
        parts = hotkey.split('+')
        
        # Определить основную клавишу и требуемые модификаторы
        main_key = None
        required_modifiers = set()
        
        for part in parts:
            part_lower = part.lower()
            if part_lower in ['shift', 'ctrl', 'alt']:
                required_modifiers.add('left ' + part_lower)
            else:
                # Основная клавиша - сохраняем регистр из хоткея
                main_key = part
        
        # Проверить основную клавишу (с учетом регистра)
        if main_key != pressed_key:
            return False
        
        # Проверить модификаторы
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

    def set_recording_mode(self, enabled: bool):
        """Режим записи - отключает срабатывание хоткеев"""
        self.recording_mode = enabled
    
    def bind(self, hotkey: str, action_id: str):
        """Привязать хоткей к действию"""
        # Отвязать старый хоткей если был
        old_hotkey = self._find_hotkey_by_action(action_id)
        if old_hotkey and old_hotkey != hotkey:
            self.unbind(old_hotkey)
        
        # Если хоткей занят - освободить
        if hotkey in self.bindings:
            old_action = self.bindings[hotkey]
            if old_action != action_id:
                logging.info(f"Hotkey {hotkey} reassigned from {old_action} to {action_id}")
        
        # Привязать новый
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
    
    def _convert_to_keyboard_format(self, hotkey: str) -> str:
        """
        Конвертировать формат хоткея для библиотеки keyboard
        "Shift+Y" -> "left shift+y"
        "Ctrl+Alt+X" -> "left ctrl+left alt+x"
        """
        parts = hotkey.split('+')
        converted = []
        
        for part in parts:
            part_lower = part.lower()
            
            # Модификаторы - добавляем "left"
            if part_lower == 'shift':
                converted.append('left shift')
            elif part_lower == 'ctrl':
                converted.append('left ctrl')
            elif part_lower == 'alt':
                converted.append('left alt')
            else:
                # Обычная клавиша - в нижний регистр
                converted.append(part_lower)
        
        return '+'.join(converted)
    
    def _check_modifiers_match(self, hotkey: str) -> bool:
        """
        Проверить, что модификаторы соответствуют хоткею
        Если хоткей "Y" - модификаторы (Shift/Ctrl/Alt) должны быть не нажаты
        Если хоткей "Shift+Y" - должен быть нажат только Shift
        Обычные клавиши (W, A, S и т.д.) не влияют на проверку
        """
        parts = hotkey.split('+')
        required_mods = set()
        
        for part in parts:
            part_lower = part.lower()
            if part_lower == 'shift':
                required_mods.add('left shift')
            elif part_lower == 'ctrl':
                required_mods.add('left ctrl')
            elif part_lower == 'alt':
                required_mods.add('left alt')
        
        # Проверить только модификаторы
        # Если модификатор нажат, но не требуется - блокировать
        # Если модификатор требуется, но не нажат - блокировать
        for mod in ['left shift', 'left ctrl', 'left alt']:
            is_pressed = self.modifiers.get(mod, False)
            is_required = mod in required_mods
            
            if is_pressed and not is_required:
                # Модификатор нажат, но не нужен
                return False
            if is_required and not is_pressed:
                # Модификатор нужен, но не нажат
                return False
        
        return True
    
    def _on_hotkey_pressed(self, action_id: str):
        """Обработчик срабатывания хоткея"""
        # Игнорировать в режиме записи
        if self.recording_mode:
            return
        
        # Найти хоткей для этого действия
        hotkey = self.get_hotkey_for_action(action_id)
        
        # Проверить модификаторы (для точного совпадения)
        if not self._check_modifiers_match(hotkey):
            return
        
        logging.info(f"Hotkey pressed for action: {action_id}")
        
        # Выполнить действие в главном потоке GUI
        try:
            self.action_manager.execute(action_id)
        except Exception as e:
            logging.error(f"Error executing action {action_id}: {e}")
    
    def stop(self):
        """Остановить менеджер"""
        self.unbind_all()
        try:
            keyboard.unhook_all()
        except:
            pass
        logging.info("Hotkey manager stopped")