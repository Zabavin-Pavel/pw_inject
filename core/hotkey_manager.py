"""
Менеджер хоткеев с использованием Windows API
Поддержка только Left Shift, Left Alt, Left Ctrl
"""
import logging
import ctypes
import threading
from ctypes import wintypes

# Windows API константы
WH_KEYBOARD_LL = 13
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_SYSKEYDOWN = 0x0104
WM_SYSKEYUP = 0x0105

# Virtual Key Codes
VK_LSHIFT = 0xA0
VK_LCONTROL = 0xA2
VK_LMENU = 0xA4  # Left Alt

# Структура для low-level keyboard hook
class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode", wintypes.DWORD),
        ("scanCode", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(wintypes.ULONG))
    ]

HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_int, wintypes.WPARAM, ctypes.POINTER(KBDLLHOOKSTRUCT))

class HotkeyManager:
    """Менеджер глобальных хоткеев с точным контролем модификаторов"""
    
    def __init__(self, action_manager):
        self.action_manager = action_manager
        self.bindings = {}  # {hotkey_string: action_id}
        
        # Состояние клавиш
        self.pressed_keys = set()  # Обычные клавиши
        self.modifiers_state = {
            'Shift': False,
            'Ctrl': False,
            'Alt': False
        }
        
        # Флаг для отключения обработки во время записи
        self.recording_mode = False
        
        # Hook
        self.hook_id = None
        self.hook_proc = None
        self.running = False
        
        # GUI callback для вызова в главном потоке
        self.gui_callback = None
        
        # Запуск хука
        self._start_hook()
    
    def set_gui_callback(self, callback):
        """
        Установить callback для вызова из GUI потока
        callback должен принимать функцию и вызывать её в главном потоке
        Например: lambda func: root.after(0, func)
        """
        self.gui_callback = callback
    
    def set_recording_mode(self, enabled: bool):
        """Включить/выключить режим записи (отключает срабатывание хоткеев)"""
        self.recording_mode = enabled
    
    def bind(self, hotkey: str, action_id: str):
        """
        Привязать хоткей к действию
        
        Args:
            hotkey: Комбинация клавиш (например "Shift+R" или "R")
            action_id: ID действия
        """
        # Отвязать старый хоткей если был
        old_hotkey = self._find_hotkey_by_action(action_id)
        if old_hotkey and old_hotkey != hotkey:
            self.unbind(old_hotkey)
        
        # Если хоткей уже занят другим действием - освободить
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
    
    def _start_hook(self):
        """Запустить keyboard hook"""
        def hook_thread():
            self.hook_proc = HOOKPROC(self._keyboard_hook)
            self.hook_id = ctypes.windll.user32.SetWindowsHookExA(
                WH_KEYBOARD_LL,
                self.hook_proc,
                ctypes.windll.kernel32.GetModuleHandleW(None),
                0
            )
            
            if not self.hook_id:
                logging.error("Failed to install keyboard hook")
                return
            
            self.running = True
            logging.info("Keyboard hook installed")
            
            # Message loop
            msg = wintypes.MSG()
            while self.running:
                result = ctypes.windll.user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
                if result <= 0:
                    break
                ctypes.windll.user32.TranslateMessage(ctypes.byref(msg))
                ctypes.windll.user32.DispatchMessageW(ctypes.byref(msg))
        
        self.hook_thread = threading.Thread(target=hook_thread, daemon=True)
        self.hook_thread.start()
    
    def _keyboard_hook(self, nCode, wParam, lParam):
        """Low-level keyboard hook callback"""
        if nCode >= 0:
            kb = lParam.contents
            vk_code = kb.vkCode
            
            # Определяем событие
            is_keydown = wParam in (WM_KEYDOWN, WM_SYSKEYDOWN)
            is_keyup = wParam in (WM_KEYUP, WM_SYSKEYUP)
            
            if is_keydown:
                self._on_key_down(vk_code)
            elif is_keyup:
                self._on_key_up(vk_code)
        
        return ctypes.windll.user32.CallNextHookEx(self.hook_id, nCode, wParam, lParam)
    
    def _on_key_down(self, vk_code: int):
        """Обработка нажатия клавиши"""
        # Обновляем состояние модификаторов
        if vk_code == VK_LSHIFT:
            self.modifiers_state['Shift'] = True
        elif vk_code == VK_LCONTROL:
            self.modifiers_state['Ctrl'] = True
        elif vk_code == VK_LMENU:
            self.modifiers_state['Alt'] = True
        else:
            # Обычная клавиша
            key_name = self._vk_to_string(vk_code)
            if key_name and key_name not in self.pressed_keys:
                self.pressed_keys.add(key_name)
                
                # Не проверяем хоткеи в режиме записи
                if not self.recording_mode:
                    self._check_hotkey_trigger()
    
    def _on_key_up(self, vk_code: int):
        """Обработка отпускания клавиши"""
        # Обновляем состояние модификаторов
        if vk_code == VK_LSHIFT:
            self.modifiers_state['Shift'] = False
        elif vk_code == VK_LCONTROL:
            self.modifiers_state['Ctrl'] = False
        elif vk_code == VK_LMENU:
            self.modifiers_state['Alt'] = False
        else:
            # Обычная клавиша
            key_name = self._vk_to_string(vk_code)
            if key_name:
                self.pressed_keys.discard(key_name)
    
    def _check_hotkey_trigger(self):
        """Проверить, сработал ли какой-то хоткей"""
        # Строим текущую комбинацию
        current_hotkey = self._build_current_hotkey()
        
        if not current_hotkey:
            return
        
        logging.debug(f"Current hotkey combination: {current_hotkey}")
        logging.debug(f"Available bindings: {list(self.bindings.keys())}")
        
        # Проверяем точное совпадение
        if current_hotkey in self.bindings:
            action_id = self.bindings[current_hotkey]
            logging.info(f"✓ Hotkey triggered: '{current_hotkey}' -> '{action_id}'")
            self._on_hotkey_pressed(action_id)
        else:
            logging.debug(f"✗ No binding for: '{current_hotkey}'")
    
    def _build_current_hotkey(self) -> str:
        """
        Построить строку текущей комбинации клавиш
        Формат: "Shift+R", "Ctrl+Alt+X", "R" и т.д.
        """
        parts = []
        
        # Добавляем модификаторы в правильном порядке
        if self.modifiers_state['Ctrl']:
            parts.append('Ctrl')
        if self.modifiers_state['Shift']:
            parts.append('Shift')
        if self.modifiers_state['Alt']:
            parts.append('Alt')
        
        # Добавляем обычные клавиши (берём последнюю нажатую)
        if self.pressed_keys:
            # Если нажато несколько клавиш, берём только последнюю
            last_key = list(self.pressed_keys)[-1]
            parts.append(last_key)
        
        return '+'.join(parts) if parts else ""
    
    def _vk_to_string(self, vk_code: int) -> str:
        """Преобразовать Virtual Key Code в строку"""
        # A-Z (0x41-0x5A)
        if 0x41 <= vk_code <= 0x5A:
            return chr(vk_code)
        
        # 0-9 (0x30-0x39)
        if 0x30 <= vk_code <= 0x39:
            return chr(vk_code)
        
        # F1-F12
        if 0x70 <= vk_code <= 0x7B:
            return f"F{vk_code - 0x6F}"
        
        # Дополнительные клавиши
        special_keys = {
            0x20: 'Space',
            0x0D: 'Return',
            0x1B: 'Escape',
            0x09: 'Tab',
            0x08: 'BackSpace',
        }
        
        return special_keys.get(vk_code, None)
    
    def _on_hotkey_pressed(self, action_id: str):
        """Обработчик срабатывания хоткея"""
        logging.info(f"Hotkey pressed for action: {action_id}")
        
        # Если есть GUI callback - используем его для вызова в главном потоке
        if self.gui_callback:
            self.gui_callback(lambda: self.action_manager.execute(action_id))
        else:
            # Прямой вызов (может не работать из hook потока)
            self.action_manager.execute(action_id)
    
    def stop(self):
        """Остановить hook"""
        self.running = False
        if self.hook_id:
            ctypes.windll.user32.UnhookWindowsHookEx(self.hook_id)
            self.hook_id = None
            logging.info("Keyboard hook removed")