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
        self.registered_hotkeys = set()
        
        # Для режима записи
        self.recording_mode = False
        
        # Хук для отслеживания состояния модификаторов
        self._setup_modifier_tracking()
    
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
        
        # Отслеживать только левые модификаторы
        if key_name in self.modifiers:
            self.modifiers[key_name] = (event.event_type == 'down')
    
    def set_recording_mode(self, enabled: bool):
        """Режим записи - отключает срабатывание хоткеев"""
        self.recording_mode = enabled
    
    def bind(self, hotkey: str, action_id: str):
        """
        Привязать хоткей к действию
        
        Args:
            hotkey: Комбинация (например "Shift+Y")
            action_id: ID действия
        """
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
        
        # Конвертировать в формат keyboard
        keyboard_hotkey = self._convert_to_keyboard_format(hotkey)
        
        # Зарегистрировать
        try:
            keyboard.add_hotkey(
                keyboard_hotkey,
                lambda aid=action_id: self._on_hotkey_pressed(aid),
                suppress=False
            )
            self.registered_hotkeys.add(hotkey)
            logging.info(f"Bound hotkey '{hotkey}' to action '{action_id}'")
        except Exception as e:
            logging.error(f"Failed to bind hotkey {hotkey}: {e}")
    
    def unbind(self, hotkey: str):
        """Отвязать хоткей"""
        if hotkey in self.bindings:
            action_id = self.bindings.pop(hotkey)
            
            # Удалить из keyboard
            if hotkey in self.registered_hotkeys:
                try:
                    keyboard_hotkey = self._convert_to_keyboard_format(hotkey)
                    keyboard.remove_hotkey(keyboard_hotkey)
                    self.registered_hotkeys.remove(hotkey)
                    logging.info(f"Unbound hotkey '{hotkey}' from action '{action_id}'")
                except Exception as e:
                    logging.warning(f"Failed to unbind hotkey {hotkey}: {e}")
    
    def unbind_all(self):
        """Отвязать все хоткеи"""
        for hotkey in list(self.registered_hotkeys):
            try:
                keyboard_hotkey = self._convert_to_keyboard_format(hotkey)
                keyboard.remove_hotkey(keyboard_hotkey)
            except:
                pass
        
        self.bindings.clear()
        self.registered_hotkeys.clear()
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
        Если хоткей "Y" - модификаторы должны быть не нажаты
        Если хоткей "Shift+Y" - должен быть нажат только Shift
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
        
        # Проверить, что нажаты ТОЛЬКО требуемые модификаторы
        for mod, is_pressed in self.modifiers.items():
            if is_pressed and mod not in required_mods:
                return False
            if not is_pressed and mod in required_mods:
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