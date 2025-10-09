"""
Состояние приложения
"""

class AppState:
    """Центральное хранилище состояния приложения"""
    
    def __init__(self):
        # Персонажи
        self.selected_character = None  # Character или None (оранжевая подсветка)
        self.active_characters = set()  # {Character, ...} (цветные иконки)
        
        # Верификация
        self.verified = False
        
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
    
    def toggle_action(self, action_id):
        """Переключить toggle-действие"""
        if action_id in self.active_toggle_actions:
            self.active_toggle_actions.remove(action_id)
        else:
            self.active_toggle_actions.add(action_id)
    
    def is_action_active(self, action_id):
        """Проверить активно ли действие"""
        return action_id in self.active_toggle_actions