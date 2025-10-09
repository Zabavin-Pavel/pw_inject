"""
Панель хоткеев и действий
"""
import tkinter as tk
from gui.styles import *

class HotkeyPanel(tk.Frame):
    """Панель хоткеев и иконок действий"""
    
    def __init__(self, parent, app_state, action_manager, hotkey_manager, settings_manager, on_action_executed):
        super().__init__(parent, bg=COLOR_BG)
        
        self.app_state = app_state
        self.action_manager = action_manager
        self.hotkey_manager = hotkey_manager
        self.settings_manager = settings_manager
        self.on_action_executed = on_action_executed
        
        self.icon_buttons = {}    # {action_id: IconButton}
        self.hotkey_rows = {}     # {action_id: HotkeyRow}
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Создать UI"""
        # === Верхняя часть: иконки действий (toggle) ===
        self.icons_container = tk.Frame(self, bg=COLOR_BG)
        self.icons_container.pack(fill=tk.X, padx=0, pady=(10, 15))
        
        # Центрирование иконок
        spacer_left = tk.Frame(self.icons_container, bg=COLOR_BG)
        spacer_left.pack(side=tk.LEFT, expand=True)
        
        # Создать кнопки для действий с иконками
        icon_actions = self.action_manager.get_icon_actions()
        for action in icon_actions:
            btn = IconButton(
                self.icons_container,
                action,
                self.app_state,
                lambda aid=action.id: self._on_icon_clicked(aid)
            )
            btn.pack(side=tk.LEFT, padx=8)
            self.icon_buttons[action.id] = btn
        
        spacer_right = tk.Frame(self.icons_container, bg=COLOR_BG)
        spacer_right.pack(side=tk.LEFT, expand=True)
        
        # === Нижняя часть: хоткеи ===
        self.hotkeys_container = tk.Frame(self, bg=COLOR_BG)
        self.hotkeys_container.pack(fill=tk.BOTH, expand=True, padx=0, pady=(0, 10))
        
        # Создать строки для действий с хоткеями
        hotkey_actions = self.action_manager.get_hotkey_actions()
        for action in hotkey_actions:
            row = HotkeyRow(
                self.hotkeys_container,
                action,
                self.hotkey_manager,
                self.settings_manager,
                lambda aid=action.id: self._on_hotkey_action_executed(aid),
                on_hotkey_changed=self._on_hotkey_changed
            )
            row.pack(fill=tk.X, pady=2)
            self.hotkey_rows[action.id] = row
    
    def _on_icon_clicked(self, action_id: str):
        """Клик по иконке действия"""
        action = self.action_manager.get_action(action_id)
        
        if action.type == 'toggle':
            # Toggle действие - переключить состояние
            self.app_state.toggle_action(action_id)
        
        # Выполнить действие
        self.on_action_executed(action_id)
        
        # Обновить отображение
        if action_id in self.icon_buttons:
            self.icon_buttons[action_id].update_display()
    
    def _on_hotkey_action_executed(self, action_id: str):
        """Выполнение действия через кнопку или хоткей"""
        self.on_action_executed(action_id)
    
    def _on_hotkey_changed(self):
        """Callback когда хоткей изменился - обновить все UI"""
        self.update_hotkey_display()
    
    def update_display(self):
        """Обновить отображение всех элементов"""
        # Обновить иконки
        for btn in self.icon_buttons.values():
            btn.update_display()
    
    def update_hotkey_display(self):
        """Обновить отображение ВСЕХ хоткеев в UI"""
        for action_id, row in self.hotkey_rows.items():
            row.refresh_hotkey_display()
    
    def flash_action(self, action_id: str):
        """Мигнуть действием (оранжевая подсветка ТЕКСТА)"""
        if action_id in self.hotkey_rows:
            self.hotkey_rows[action_id].flash_text()


class IconButton(tk.Label):
    """Кнопка-иконка для toggle действия"""
    
    def __init__(self, parent, action, app_state, on_clicked):
        super().__init__(
            parent,
            text=action.icon,
            font=("Segoe UI", 20),  # Размер иконок (пункт 4)
            bg=COLOR_BG,
            fg=COLOR_TEXT,
            cursor="hand2"
        )
        
        self.action = action
        self.app_state = app_state
        self.on_clicked = on_clicked
        
        self.bind("<Button-1>", lambda e: self._on_click())
        
        self.update_display()
    
    def _on_click(self):
        """Клик - вызвать callback (мигание в HotkeyRow)"""
        self.on_clicked()
    
    def update_display(self):
        """Обновить отображение кнопки"""
        is_active = self.app_state.is_action_active(self.action.id)
        
        if is_active:
            self.configure(fg=COLOR_ACCENT)
        else:
            self.configure(fg=COLOR_TEXT)


class HotkeyRow(tk.Frame):
    """Строка с названием действия и полем хоткея"""
    
    def __init__(self, parent, action, hotkey_manager, settings_manager, on_executed, on_hotkey_changed):
        super().__init__(parent, bg=COLOR_BG, highlightthickness=0)
        
        self.action = action
        self.hotkey_manager = hotkey_manager
        self.settings_manager = settings_manager
        self.on_executed = on_executed
        self.on_hotkey_changed = on_hotkey_changed
        
        self.recording = False
        self.pressed_keys = set()
        
        # НОВОЕ: Переменная для отслеживания анимации
        self.is_flashing = False
        self.flash_job = None
        
        # Маппинг русских букв на английские
        self.ru_to_en = {
            'й': 'q', 'ц': 'w', 'у': 'e', 'к': 'r', 'е': 't', 'н': 'y', 'г': 'u', 'ш': 'i', 'щ': 'o', 'з': 'p',
            'х': '[', 'ъ': ']', 'ф': 'a', 'ы': 's', 'в': 'd', 'а': 'f', 'п': 'g', 'р': 'h', 'о': 'j', 'л': 'k',
            'д': 'l', 'ж': ';', 'э': "'", 'я': 'z', 'ч': 'x', 'с': 'c', 'м': 'v', 'и': 'b', 'т': 'n', 'ь': 'm',
            'б': ',', 'ю': '.'
        }
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Создать UI строки"""
        # Название действия (кликабельное)
        label_text = self.action.label
        if len(label_text) > MAX_ACTION_LENGTH:
            label_text = label_text[:MAX_ACTION_LENGTH-3] + "..."
        
        self.action_label = tk.Label(
            self,
            text=label_text,
            font=FONT_MAIN,
            bg=COLOR_BG,
            fg=COLOR_TEXT,
            anchor="w",
            cursor="hand2"
        )
        self.action_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.action_label.bind("<Button-1>", lambda e: self._on_label_click())
        
        # Поле хоткея
        current_hotkey = self.hotkey_manager.get_hotkey_for_action(self.action.id)
        
        self.hotkey_entry = tk.Entry(
            self,
            width=10,
            font=FONT_HOTKEY,
            bg=COLOR_BG_LIGHT,
            fg=COLOR_TEXT_BRIGHT,
            insertbackground=COLOR_TEXT_BRIGHT,
            relief=tk.SOLID,
            justify=tk.CENTER,
            bd=1,
            highlightthickness=1,
            highlightbackground=COLOR_BORDER,
            highlightcolor=COLOR_BORDER
        )
        self.hotkey_entry.pack(side=tk.RIGHT, padx=(10, 0))
        self.hotkey_entry.insert(0, current_hotkey if current_hotkey else "-")
        
        # Обработчики
        self.hotkey_entry.bind("<FocusIn>", self._on_focus_in)
        self.hotkey_entry.bind("<FocusOut>", self._on_focus_out)
        self.hotkey_entry.bind("<KeyPress>", self._on_key_press)
        self.hotkey_entry.bind("<KeyRelease>", self._on_key_release)
        self.hotkey_entry.bind("<Button-3>", self._on_right_click)
    
    def refresh_hotkey_display(self):
        """Обновить отображение хоткея из HotkeyManager"""
        if self.recording:
            return
        
        current_hotkey = self.hotkey_manager.get_hotkey_for_action(self.action.id)
        self.hotkey_entry.delete(0, tk.END)
        self.hotkey_entry.insert(0, current_hotkey if current_hotkey else "-")
    
    def _on_label_click(self):
        """Клик по названию - выполнить и мигнуть ТЕКСТОМ"""
        self.on_executed()
        self.flash_text()
    
    def _on_focus_in(self, event):
        """Фокус на поле - начало записи"""
        self.recording = True
        self.pressed_keys.clear()
        
        self.hotkey_entry.configure(
            highlightbackground=COLOR_ACCENT,
            highlightcolor=COLOR_ACCENT
        )
        self.hotkey_entry.delete(0, tk.END)
        self.hotkey_entry.insert(0, "...")
    
    def _on_focus_out(self, event):
        """Потеря фокуса - конец записи"""
        self.recording = False
        self.pressed_keys.clear()
        
        self.hotkey_entry.configure(
            highlightbackground=COLOR_BORDER,
            highlightcolor=COLOR_BORDER
        )
        
        self.refresh_hotkey_display()
    
    def _on_right_click(self, event):
        """ПКМ - очистить хоткей или прервать запись"""
        if self.recording:
            self.hotkey_entry.master.focus_set()
        else:
            self._clear_hotkey()
        
        return "break"
    
    def _clear_hotkey(self):
        """Очистить хоткей"""
        old_hotkey = self.hotkey_manager.get_hotkey_for_action(self.action.id)
        if old_hotkey:
            self.hotkey_manager.unbind(old_hotkey)
        
        hotkeys = self.settings_manager.get_hotkeys()
        hotkeys[self.action.id] = "-"
        self.settings_manager.set_hotkeys(hotkeys)
        
        self.hotkey_entry.delete(0, tk.END)
        self.hotkey_entry.insert(0, "-")
        
        self.flash_border()
    
    def _on_key_press(self, event):
        """Нажатие клавиши"""
        if not self.recording:
            return "break"
        
        key = self._normalize_key(event.keysym, event.char)
        
        if key:
            self.pressed_keys.add(key)
        
        self._update_display()
        
        return "break"
    
    def _on_key_release(self, event):
        """Отпускание клавиши"""
        if not self.recording:
            return "break"
        
        if len(self.pressed_keys) > 0:
            hotkey = self._build_hotkey_string()
            
            if hotkey:
                self._save_hotkey(hotkey)
                self.hotkey_entry.master.focus_set()
        
        return "break"
    
    def _normalize_key(self, keysym: str, char: str) -> str:
        """Нормализовать имя клавиши"""
        modifier_map = {
            'Control_L': 'Ctrl', 'Control_R': 'Ctrl',
            'Shift_L': 'Shift', 'Shift_R': 'Shift',
            'Alt_L': 'Alt', 'Alt_R': 'Alt',
            'Win_L': 'Win', 'Win_R': 'Win',
        }
        
        if keysym in modifier_map:
            return modifier_map[keysym]
        
        if char and char.lower() in self.ru_to_en:
            return self.ru_to_en[char.lower()].upper()
        
        return keysym.capitalize() if len(keysym) == 1 else keysym
    
    def _build_hotkey_string(self) -> str:
        """Собрать строку хоткея"""
        if not self.pressed_keys:
            return ""
        
        modifiers_order = ['Ctrl', 'Shift', 'Alt', 'Win']
        
        modifiers = []
        keys = []
        
        for key in self.pressed_keys:
            if key in modifiers_order:
                modifiers.append(key)
            else:
                keys.append(key)
        
        modifiers.sort(key=lambda x: modifiers_order.index(x))
        
        parts = modifiers + keys
        return '+'.join(parts)
    
    def _update_display(self):
        """Обновить отображение в поле"""
        hotkey = self._build_hotkey_string()
        
        self.hotkey_entry.delete(0, tk.END)
        self.hotkey_entry.insert(0, hotkey if hotkey else "...")
    
    def _save_hotkey(self, hotkey: str):
        """Сохранить хоткей"""
        try:
            # Если хоткей уже используется - очистить у старого
            old_action_id = self.hotkey_manager.bindings.get(hotkey)
            if old_action_id and old_action_id != self.action.id:
                self.hotkey_manager.unbind(hotkey)
                
                hotkeys = self.settings_manager.get_hotkeys()
                hotkeys[old_action_id] = "-"
                self.settings_manager.set_hotkeys(hotkeys)
            
            # Привязать новый хоткей
            self.hotkey_manager.bind(hotkey, self.action.id)
            
            # Сохранить в настройки
            hotkeys = self.settings_manager.get_hotkeys()
            hotkeys[self.action.id] = hotkey
            self.settings_manager.set_hotkeys(hotkeys)
            
            # Обновить UI всех строк
            if self.on_hotkey_changed:
                self.on_hotkey_changed()
            
        except Exception as e:
            self.hotkey_entry.delete(0, tk.END)
            self.hotkey_entry.insert(0, "ERROR")
            self.hotkey_entry.after(1000, lambda: self._on_focus_out(None))
    
    def flash_text(self):
        """Мигнуть ТЕКСТОМ (НОВЫЙ ПОДХОД - отменяет предыдущую анимацию)"""
        # Отменить предыдущую анимацию
        if self.flash_job:
            try:
                self.after_cancel(self.flash_job)
            except:
                pass
            self.flash_job = None
        
        self.is_flashing = True
        
        # ВСЕГДА использовать COLOR_TEXT как базовый
        base_color = COLOR_TEXT
        
        # Подсветить
        self.action_label.configure(fg=COLOR_ACCENT)
        
        # Вернуть
        def restore():
            self.action_label.configure(fg=base_color)
            self.is_flashing = False
            self.flash_job = None
        
        self.flash_job = self.after(250, restore)
    
    def flash_border(self):
        """Мигнуть РАМКОЙ"""
        self.hotkey_entry.configure(
            highlightbackground=COLOR_ACCENT,
            highlightcolor=COLOR_ACCENT
        )
        
        self.after(150, lambda: self.hotkey_entry.configure(
            highlightbackground=COLOR_BORDER,
            highlightcolor=COLOR_BORDER
        ))