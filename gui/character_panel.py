"""
Панель персонажей - БЕЗОПАСНАЯ ВЕРСИЯ
"""
import tkinter as tk
from PIL import Image, ImageTk
import logging
import ctypes
from ctypes import wintypes
from gui.styles import *

class CharacterPanel(tk.Frame):
    """Панель списка персонажей"""
    
    def __init__(self, parent, app_state, on_character_selected, on_character_toggled):
        super().__init__(parent, bg=COLOR_BG)
        
        self.app_state = app_state
        self.on_character_selected = on_character_selected
        self.on_character_toggled = on_character_toggled
        
        self.characters = []
        self.character_rows = {}
        self.class_icons = {}
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Создать UI"""
        self.characters_container = tk.Frame(self, bg=COLOR_BG)
        self.characters_container.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
    
    def set_characters(self, characters):
        """Установить список персонажей"""
        # Очистить старые строки
        for widget in self.characters_container.winfo_children():
            widget.destroy()
        
        self.characters = characters
        self.character_rows.clear()
        
        # Создать строки для каждого персонажа
        for character in characters:
            row = CharacterRow(
                self.characters_container,
                character,
                self.app_state,
                self._load_class_icons(character.char_base.char_class),
                self.on_character_selected,
                on_icon_clicked=self._on_icon_clicked
            )
            # НОВОЕ: Передаем ссылку на менеджера для доступа к party_cache
            if hasattr(character, 'manager'):
                row.character.manager = character.manager

            row.pack(fill=tk.X, padx=2, pady=0)
            self.character_rows[character] = row
    
    def update_display(self):
        """Обновить отображение всех персонажей"""
        for character, row in self.character_rows.items():
            row.update_display()
    
    def _on_icon_clicked(self, character):
        """Клик по иконке - активировать окно персонажа"""
        try:
            pid = character.pid
            
            # Простой и безопасный способ через EnumWindows
            user32 = ctypes.windll.user32
            
            found_hwnd = None
            
            def callback(hwnd, lParam):
                nonlocal found_hwnd
                
                if user32.IsWindowVisible(hwnd):
                    # Получить PID окна
                    process_id = wintypes.DWORD()
                    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id))
                    
                    if process_id.value == pid:
                        # Получить заголовок окна
                        length = user32.GetWindowTextLengthW(hwnd)
                        if length > 0:
                            buff = ctypes.create_unicode_buffer(length + 1)
                            user32.GetWindowTextW(hwnd, buff, length + 1)
                            
                            # Проверить что это окно игры (есть заголовок)
                            if buff.value:
                                found_hwnd = hwnd
                                return False  # Остановить перечисление
                
                return True  # Продолжить
            
            # Создать callback
            EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
            enum_proc = EnumWindowsProc(callback)
            
            # Перечислить окна
            user32.EnumWindows(enum_proc, 0)
            
            if found_hwnd:
                # Активировать окно
                # SW_RESTORE = 9
                user32.ShowWindow(found_hwnd, 9)
                user32.SetForegroundWindow(found_hwnd)
                
                logging.info(f"Activated window for character {character.char_base.char_name} (HWND: {found_hwnd})")
            else:
                logging.warning(f"Window not found for PID {pid}")
                
        except Exception as e:
            logging.error(f"Failed to activate window: {e}", exc_info=True)
    
    def _load_class_icons(self, class_id: int):
        """Загрузить иконку класса (цветную и серую)"""
        if class_id in self.class_icons:
            return self.class_icons[class_id]
        
        try:
            icon_path = f"{ICONS_PATH}/{class_id}.png"
            image = Image.open(icon_path)
            image = image.resize((ICON_SIZE, ICON_SIZE), Image.Resampling.LANCZOS)
            
            # Цветная версия
            color_photo = ImageTk.PhotoImage(image)
            
            # Серая версия (не используется, но оставляем)
            gray_image = image.convert('L')
            gray_photo = ImageTk.PhotoImage(gray_image)
            
            self.class_icons[class_id] = (color_photo, gray_photo)
            
            logging.info(f"Загружена иконка {class_id}")
            
            return (color_photo, gray_photo)
        
        except Exception as e:
            logging.warning(f"Failed to load class icon {class_id}: {e}")
            return (None, None)


class CharacterRow(tk.Frame):
    """Строка персонажа с иконкой и именем"""
    
    def __init__(self, parent, character, app_state, icons, on_selected, on_icon_clicked):
        super().__init__(parent, bg=COLOR_BG, highlightthickness=0)
        
        self.character = character
        self.app_state = app_state
        self.color_icon, self.gray_icon = icons  # Распаковываем кортеж
        self.on_selected = on_selected
        self.on_icon_clicked = on_icon_clicked
        
        self.is_flashing = False
        self.flash_job = None
    
        # НОВОЕ: Кешируем последний цвет ника для оптимизации
        self.last_nick_color = COLOR_TEXT
        
        # Иконка класса (ВСЕГДА ЦВЕТНАЯ)
        if self.color_icon:
            self.icon_label = tk.Label(
                self,
                image=self.color_icon,
                bg=COLOR_BG,
                cursor="hand2"
            )
            self.icon_label.pack(side=tk.LEFT, padx=(2, 0))
            self.icon_label.bind("<Button-1>", lambda e: self._on_icon_click())
        
        # Имя персонажа (кликабельное для переключения окна)
        char_name = self.character.char_base.char_name
        display_name = char_name
        
        # Добавить огненную иконку для особых персонажей
        if any(keyword in char_name.lower() for keyword in ['fire', 'flame', 'inn', 'rin']):
            display_name = f"🔥{char_name}"

        if len(display_name) > MAX_NAME_LENGTH:
            display_name = display_name[:MAX_NAME_LENGTH-3] + "..."
        
        self.name_label = tk.Label(
            self,
            text=display_name,
            font=("Segoe UI", 9, "bold"),
            bg=COLOR_BG,
            fg=COLOR_TEXT,
            cursor="hand2",
            anchor="w",
        )
        self.name_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.name_label.bind("<Button-1>", lambda e: self._on_name_click())
    
    def _on_icon_click(self):
        """Клик по иконке - активировать окно"""
        self.on_icon_clicked(self.character)
        self.flash()
    
    def _on_name_click(self):
        """Клик по никнейму - активировать окно (как иконка)"""
        self.on_icon_clicked(self.character)
        self.flash()
    
    def flash(self):
        """Мигнуть никнеймом (как экшены)"""
        if self.is_flashing:
            return
        
        self.is_flashing = True
        original_fg = self.name_label.cget('fg')
        
        # Мигаем: акцент -> оригинал -> акцент -> оригинал
        self.name_label.configure(fg=COLOR_ACCENT)
        self.flash_job = self.after(100, lambda: self.name_label.configure(fg=original_fg))
        self.flash_job = self.after(200, lambda: self.name_label.configure(fg=COLOR_ACCENT))
        self.flash_job = self.after(300, lambda: self._finish_flash(original_fg))
    
    def _finish_flash(self, original_fg):
        """Завершить мигание"""
        self.name_label.configure(fg=original_fg)
        self.is_flashing = False
    
    def update_display(self):
        """Обновить отображение строки с учетом роли в группе"""
        # Фон ВСЕГДА остаётся тёмным
        self.configure(bg=COLOR_BG)
        if hasattr(self, 'icon_label'):
            self.icon_label.configure(bg=COLOR_BG)
        self.name_label.configure(bg=COLOR_BG)
        
        # НОВОЕ: Определяем цвет ника в зависимости от роли
        new_fg = COLOR_TEXT  # По умолчанию серый
        
        # Получаем кеш группы из менеджера
        if hasattr(self.character, 'manager') and self.character.manager:
            party_cache = self.character.manager._get_party_cache()
            
            leader = party_cache.get('leader')
            members = party_cache.get('members', [])
            
            # Проверяем роль персонажа
            if leader and self.character.char_base.char_id == leader.char_base.char_id:
                new_fg = COLOR_LEADER  # Желтый для лидера
            elif any(m.char_base.char_id == self.character.char_base.char_id for m in members):
                new_fg = COLOR_MEMBER  # Зеленый для члена группы
            # НОВОЕ: Если нет лидера - выделяем активное окно желтым
            elif not leader and self.app_state.last_active_character:
                if self.character.pid == self.app_state.last_active_character.pid:
                    new_fg = COLOR_LEADER  # Желтый для активного окна
        
        # Применяем цвет
        self.name_label.configure(fg=new_fg)