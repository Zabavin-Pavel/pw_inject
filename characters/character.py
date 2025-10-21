"""
Модель персонажа - ОБНОВЛЕНО
Добавлено кеширование fly trigger состояний
"""
# from characters.behaviors import CharacterBehavior
import logging

class Character:
    """Представление одного игрового персонажа"""
    
    def __init__(self, pid, memory, char_base):
        self.pid = pid
        self.memory = memory
        self.char_base = char_base
        self.manager = None  # НОВОЕ: Будет установлено из CharacterManager
        
        # Поведение (класс-специфичная логика)
        # self.behavior = CharacterBehavior.for_class(char_base.char_class)
        
        # Для Follow: информация о заморозке полета
        self.fly_freeze_info = None
        
        # НОВОЕ: Кеш fly trigger состояний (для управления полетом)
        # None пока не найдены, потом {'on': int, 'off': int}
        self.fly_trigger_states = None
    
    def is_valid(self):
        """Проверка валидности персонажа"""
        return self.char_base.is_valid()
    
    def update_fly_trigger_cache(self):
        """
        Обновить кеш fly trigger состояний
        
        Логика:
        - Пока не найдены оба состояния - проверяем текущий fly_trigger
        - Сравниваем с fly_status (летит/не летит)
        - Как только найдем оба - прекращаем мониторинг
        """
        # Если уже нашли оба состояния - не проверяем
        if self.fly_trigger_states and len(self.fly_trigger_states) == 2:
            return
        
        from game.offsets import resolve_offset, OFFSETS
        
        # Читаем текущие значения
        fly_status = resolve_offset(self.memory, OFFSETS["fly_status"], self.char_base.cache)
        fly_trigger = resolve_offset(self.memory, OFFSETS["fly_trigger"], self.char_base.cache)
        
        if fly_status is None or fly_trigger is None:
            return
        
        # Инициализируем словарь если еще нет
        if self.fly_trigger_states is None:
            self.fly_trigger_states = {}
        
        # Определяем состояние и сохраняем trigger
        if fly_status == 1:  # Летит
            if 'on' not in self.fly_trigger_states:
                self.fly_trigger_states['on'] = fly_trigger
                import logging
                logging.info(f"✈️ FLY ON: PID={self.pid}, trigger={fly_trigger}")
        else:  # Не летит
            if 'off' not in self.fly_trigger_states:
                self.fly_trigger_states['off'] = fly_trigger
                import logging
                logging.info(f"🚶 FLY OFF: PID={self.pid}, trigger={fly_trigger}")
    
    def can_control_flight(self):
        """Проверить можем ли управлять полетом (найдены оба состояния)"""
        return (self.fly_trigger_states is not None and 
                'on' in self.fly_trigger_states and 
                'off' in self.fly_trigger_states)
    
    def set_flight_state(self, should_fly: bool):
        """
        Установить состояние полета
        
        Args:
            should_fly: True = летать, False = не летать
        
        Returns:
            bool: успех операции
        """
        if not self.can_control_flight():
            return False
        
        from game.offsets import resolve_offset, OFFSETS
        
        # Определяем нужное значение
        target_value = self.fly_trigger_states['on'] if should_fly else self.fly_trigger_states['off']
        
        # Получаем адрес fly_trigger
        char_base = self.char_base.cache.get("char_base")
        if not char_base:
            return False
        
        # Записываем значение
        return self.memory.write_int(char_base + 0xA58, target_value)