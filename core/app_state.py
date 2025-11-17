"""
Состояние приложения - ОБНОВЛЕНО
Добавлена мапа pid↔char_id
"""

class AppState:
    """Центральное хранилище состояния приложения"""
    
    def __init__(self):
        # Персонажи
        self.selected_character = None  # Character или None (оранжевая подсветка)
        self.active_characters = set()  # {Character, ...} (цветные иконки)
        
        # Последнее активное окно
        self.last_active_character = None  # Character последнего активного окна ElementClient.exe
    
        # НОВОЕ: Текущий лидер группы активного окна
        self.current_leader = None  # Character объект лидера или None
        
        # НОВОЕ: Мапа pid ↔ char_id (обновляется при refresh)
        self.pid_to_char_id = {}  # {pid: char_id}
        self.char_id_to_pid = {}  # {char_id: pid}
        
        # Верификация
        self.verified = False
        
        # Уровень доступа (кэшируется при refresh)
        self.permission_level = "none"  # "none" / "try" / "pro" / "dev"
        
        # Активные toggle-действия
        self.active_toggle_actions = set()  # {'follow', 'attack', ...}
    
    def select_character(self, character):
        """Выбрать персонажа (оранжевая подсветка)"""
        self.selected_character = character
    
    def toggle_character_active(self, character):
        """Переключить активность персонажа (чекбокс)"""
        if character in self.active_characters:
            self.active_characters.remove(character)
        else:
            self.active_characters.add(character)
    
    def is_character_active(self, character):
        """Проверить активен ли персонаж"""
        return character in self.active_characters
    
    def set_last_active_character(self, character):
        """Установить последнее активное окно"""
        self.last_active_character = character
    
    def update_pid_char_id_map(self, characters):
        """
        Обновить мапу pid ↔ char_id
        
        Args:
            characters: список Character объектов
        """
        self.pid_to_char_id.clear()
        self.char_id_to_pid.clear()
        
        for char in characters:
            if char.is_valid():
                pid = char.pid
                char_id = char.char_base.char_id
                
                if pid and char_id:
                    self.pid_to_char_id[pid] = char_id
                    self.char_id_to_pid[char_id] = pid
    
    def get_char_id_by_pid(self, pid):
        """Получить char_id по PID"""
        return self.pid_to_char_id.get(pid)
    
    def get_pid_by_char_id(self, char_id):
        """Получить PID по char_id"""
        return self.char_id_to_pid.get(char_id)
    
    def toggle_action(self, action_id):
        """Переключить toggle-действие"""
        if action_id in self.active_toggle_actions:
            self.active_toggle_actions.remove(action_id)
        else:
            self.active_toggle_actions.add(action_id)
    
    def is_action_active(self, action_id):
        """Проверить активно ли действие"""
        return action_id in self.active_toggle_actions
    
    def has_permission(self, required_permission: str) -> bool:
        """
        Проверить есть ли доступ к функции
        
        Args:
            required_permission: требуемый уровень ("try", "pro", "dev")
        
        Returns:
            True если текущий уровень >= требуемого
        """
        # Иерархия уровней
        PERMISSION_HIERARCHY = {
            "none": 0,
            "try": 1,
            "pro": 2,
            "dev": 3,  # <-- lowercase!
        }
        
        current_level = PERMISSION_HIERARCHY.get(self.permission_level, 0)
        required_level = PERMISSION_HIERARCHY.get(required_permission, 0)
        
        return current_level >= required_level