"""
Панель персонажей
"""
import tkinter as tk
from PIL import Image, ImageTk, ImageEnhance
import logging
from gui.styles import *

class CharacterPanel(tk.Frame):
    """Панель списка персонажей"""
    
    def __init__(self, parent, app_state, on_character_selected, on_character_toggled):
        super().__init__(parent, bg=COLOR_BG)
        
        self.app_state = app_state
        self.on_character_selected = on_character_selected  # callback(character)
        self.on_character_toggled = on_character_toggled    # callback(character)
        
        self.characters = []  # Список персонажей
        self.character_rows = {}  # {character: CharacterRow}
        self.class_icons = {}  # Кеш иконок классов {class_id: (color, gray)}
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Создать UI"""
        # Контейнер для персонажей
        self.characters_container = tk.Frame(self, bg=COLOR_BG)
        self.characters_container.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
    
    def set_characters(self, characters):
        """
        Установить список персонажей
        
        Args:
            characters: Список объектов Character
        """
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
                self.on_character_toggled
            )
            row.pack(fill=tk.X, padx=5, pady=2)
            self.character_rows[character] = row
    
    def update_display(self):
        """Обновить отображение всех персонажей"""
        for character, row in self.character_rows.items():
            row.update_display()
    
    def _load_class_icons(self, class_id: int):
        """
        Загрузить иконку класса (цветную и серую)
        
        Returns:
            (color_icon, gray_icon) tuple
        """
        if class_id in self.class_icons:
            return self.class_icons[class_id]
        
        try:
            icon_path = f"{ICONS_PATH}/{class_id}.png"
            image = Image.open(icon_path)
            image = image.resize((ICON_SIZE, ICON_SIZE), Image.Resampling.LANCZOS)
            
            # Цветная версия
            color_photo = ImageTk.PhotoImage(image)
            
            # Серая версия (grayscale)
            gray_image = image.convert('L')
            gray_photo = ImageTk.PhotoImage(gray_image)
            
            self.class_icons[class_id] = (color_photo, gray_photo)
            
            logging.info(f"Загружена иконка {class_id}")
            
            return (color_photo, gray_photo)
        
        except Exception as e:
            logging.warning(f"Failed to load class icon {class_id}: {e}")
            return (None, None)


class CharacterRow(tk.Frame):
    """Строка персонажа"""
    
    def __init__(self, parent, character, app_state, icons, on_selected, on_toggled):
        super().__init__(parent, bg=COLOR_BG, cursor="hand2")
        
        self.character = character
        self.app_state = app_state
        self.color_icon, self.gray_icon = icons
        self.on_selected = on_selected
        self.on_toggled = on_toggled
        
        self._setup_ui()
        self.update_display()
    
    def _setup_ui(self):
        """Создать UI строки"""
        # Чекбокс (активность)
        self.checkbox_var = tk.BooleanVar(value=False)
        self.checkbox = tk.Checkbutton(
            self,
            variable=self.checkbox_var,
            bg=COLOR_BG,
            activebackground=COLOR_BG,
            selectcolor=COLOR_BG,
            highlightthickness=0,
            bd=0,
            command=self._on_checkbox_clicked
        )
        self.checkbox.pack(side=tk.LEFT, padx=(5, 2))
        
        # Иконка класса
        if self.color_icon:
            self.icon_label = tk.Label(
                self,
                image=self.color_icon,
                bg=COLOR_BG,
                cursor="hand2"
            )
            self.icon_label.pack(side=tk.LEFT, padx=(0, 5))
            self.icon_label.bind("<Button-1>", self._on_row_clicked)
        
        # Имя персонажа
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
            font=FONT_MAIN,
            bg=COLOR_BG,
            fg=COLOR_TEXT,
            cursor="hand2",
            anchor="w"
        )
        self.name_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.name_label.bind("<Button-1>", self._on_row_clicked)
        
        # Клик по всей строке
        self.bind("<Button-1>", self._on_row_clicked)
    
    def _on_row_clicked(self, event=None):
        """Клик по строке - выбор персонажа"""
        self.on_selected(self.character)
    
    def _on_checkbox_clicked(self):
        """Клик по чекбоксу - переключение активности"""
        self.on_toggled(self.character)
    
    def update_display(self):
        """Обновить отображение строки"""
        # Проверка выбран ли персонаж (оранжевая подсветка)
        is_selected = self.app_state.selected_character == self.character
        
        # Проверка активен ли персонаж (чекбокс)
        is_active = self.app_state.is_character_active(self.character)
        
        # Обновить фон
        bg_color = COLOR_SELECTED if is_selected else COLOR_BG
        self.configure(bg=bg_color)
        self.checkbox.configure(bg=bg_color, activebackground=bg_color, selectcolor=bg_color)
        if hasattr(self, 'icon_label'):
            self.icon_label.configure(bg=bg_color)
        self.name_label.configure(bg=bg_color)
        
        # Обновить цвет текста (белый если выбран, иначе серый)
        text_color = COLOR_TEXT_BRIGHT if is_selected else COLOR_TEXT
        self.name_label.configure(fg=text_color)
        
        # Обновить чекбокс
        self.checkbox_var.set(is_active)
        
        # Обновить иконку (цветная если активна, серая если нет)
        if hasattr(self, 'icon_label'):
            if is_active:
                self.icon_label.configure(image=self.color_icon)
            else:
                self.icon_label.configure(image=self.gray_icon)