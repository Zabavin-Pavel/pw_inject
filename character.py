"""
Игровой персонаж
"""
from behaviors import create_behavior

class Character:
    """Обёртка над персонажем с поведением"""
    
    def __init__(self, pid, memory, char_base):
        self.pid = pid
        self.memory = memory
        self.char_base = char_base
        
        # Поведение создаётся автоматически когда узнаем класс
        self.behavior = None
        self._update_behavior()
    
    def _update_behavior(self):
        """Обновить поведение на основе класса из памяти"""
        if self.char_base.char_class is not None and self.behavior is None:
            self.behavior = create_behavior(self)
    
    def tick(self):
        """Вызывается каждый фрейм"""
        # Обновляем поведение если ещё не создано
        if self.behavior is None:
            self._update_behavior()
        
        # Вызываем логику поведения
        if self.behavior:
            self.behavior.tick()
    
    def is_valid(self):
        """Валидация персонажа"""
        # Процесс жив
        if not self.memory.is_valid():
            return False
        
        # CharBase валиден
        if not self.char_base.is_valid():
            return False
        
        return True