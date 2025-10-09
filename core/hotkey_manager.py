"""
Менеджер хоткеев
"""
import logging
import keyboard

class HotkeyManager:
    """Менеджер глобальных хоткеев"""
    
    def __init__(self, action_manager):
        self.action_manager = action_manager
        self.bindings = {}  # {hotkey: action_id}
        self.registered_hotkeys = set()  # Множество зарегистрированных хоткеев в keyboard
    
    def bind(self, hotkey: str, action_id: str):
        """
        Привязать хоткей к действию
        
        Args:
            hotkey: Комбинация клавиш (например "Shift+U")
            action_id: ID действия
        """
        # Отвязать старый хоткей если был
        old_hotkey = self._find_hotkey_by_action(action_id)
        if old_hotkey:
            self.unbind(old_hotkey)
        
        # Привязать новый
        self.bindings[hotkey] = action_id
        
        # Зарегистрировать в keyboard
        try:
            keyboard.add_hotkey(hotkey, lambda aid=action_id: self._on_hotkey_pressed(aid))
            self.registered_hotkeys.add(hotkey)
        except Exception as e:
            logging.error(f"Failed to bind hotkey {hotkey}: {e}")
    
    def unbind(self, hotkey: str):
        """Отвязать хоткей"""
        if hotkey in self.bindings:
            self.bindings.pop(hotkey)
            
            # Удалить из keyboard
            if hotkey in self.registered_hotkeys:
                try:
                    keyboard.remove_hotkey(hotkey)
                    self.registered_hotkeys.remove(hotkey)
                except:
                    pass
    
    def unbind_all(self):
        """Отвязать все хоткеи"""
        for hotkey in list(self.registered_hotkeys):
            try:
                keyboard.remove_hotkey(hotkey)
            except:
                pass
        
        self.bindings.clear()
        self.registered_hotkeys.clear()
    
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
    
    def _on_hotkey_pressed(self, action_id: str):
        """Обработчик нажатия хоткея"""
        self.action_manager.execute(action_id)