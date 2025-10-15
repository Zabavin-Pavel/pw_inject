"""
Игровые структуры для чтения/записи данных из памяти - ОБНОВЛЕНО
Добавлено: location_id, fly_trigger
"""
from game.offsets import OFFSETS, resolve_offset
import logging


class CharBase:
    """Базовая информация о персонаже"""
    
    def __init__(self, memory):
        self.memory = memory
        self.cache = {}
        self._previous_char_id = None  # для отслеживания смены персонажа
        self._update()
    
    def _update(self):
        """Обновить данные из памяти"""
        # ОТЛАДКА
        logging.info(f"DEBUG _update: module_base={hex(self.memory.module_base)}")

        # Получаем базовые адреса
        char_origin = resolve_offset(self.memory, OFFSETS["char_origin"], self.cache)
        if char_origin:
            self.cache["char_origin"] = char_origin
        
        char_base = resolve_offset(self.memory, OFFSETS["char_base"], self.cache)
        if char_base:
            self.cache["char_base"] = char_base
        
        # Читаем char_id СРАЗУ для проверки смены персонажа
        new_char_id = resolve_offset(self.memory, OFFSETS["char_id"], self.cache)
        
        # КРИТИЧНО: Проверяем смену персонажа
        if self._previous_char_id is not None and new_char_id != self._previous_char_id:
            # Персонаж сменился! Очищаем кеш указателей
            old_id = self._previous_char_id
            logging.warning(f"🔄 Character changed: {old_id} → {new_char_id}")
            self._invalidate_cache()
        
        # Обновляем предыдущий ID
        self._previous_char_id = new_char_id
        
        # Читаем все данные
        self.char_id = new_char_id
        
        # ОТЛАДКА - покажем что читается
        char_base_addr = self.cache.get("char_base", 0)
        logging.info(f"DEBUG: Trying to read from char_base={hex(char_base_addr)}")
        logging.info(f"  char_id at +0x6A8 = {new_char_id}")
        
        self.char_class = resolve_offset(self.memory, OFFSETS["char_class"], self.cache)
        logging.info(f"  char_class at +0x9D0 = {self.char_class}")
        
        self.char_name = resolve_offset(self.memory, OFFSETS["char_name"], self.cache)
        self.target_id = resolve_offset(self.memory, OFFSETS["target_id"], self.cache)
        
        # HP/MP
        self.char_hp = resolve_offset(self.memory, OFFSETS["char_hp"], self.cache)
        self.char_max_hp = resolve_offset(self.memory, OFFSETS["char_max_hp"], self.cache)
        
        # Координаты
        self.char_pos_x = resolve_offset(self.memory, OFFSETS["char_pos_x"], self.cache)
        self.char_pos_y = resolve_offset(self.memory, OFFSETS["char_pos_y"], self.cache)
        self.char_pos_z = resolve_offset(self.memory, OFFSETS["char_pos_z"], self.cache)
        
        # Полет
        self.fly_speed = resolve_offset(self.memory, OFFSETS["fly_speed"], self.cache)
        self.fly_speed_z = resolve_offset(self.memory, OFFSETS["fly_speed_z"], self.cache)
        self.fly_status = resolve_offset(self.memory, OFFSETS["fly_status"], self.cache)
        
        # НОВОЕ: Location ID
        self.location_id = resolve_offset(self.memory, OFFSETS["location_id"], self.cache)
    
    def _invalidate_cache(self):
        """Очистить кеш указателей (кроме базовых адресов)"""
        # Сохраняем базовые адреса (они не меняются при смене персонажа)
        char_origin = self.cache.get("char_origin")
        char_base = self.cache.get("char_base")
        
        # Очищаем весь кеш
        self.cache.clear()
        
        # Восстанавливаем базовые адреса
        if char_origin:
            self.cache["char_origin"] = char_origin
        if char_base:
            self.cache["char_base"] = char_base
        
        logging.info("🔄 CharBase cache invalidated (character changed)")
    
    def is_valid(self):
        """Проверка валидности данных"""
        return self.char_id is not None and self.char_id != 0
    
    def get_position(self):
        """Получить координаты (x, y, z)"""
        self._update()
        return (self.char_pos_x, self.char_pos_y, self.char_pos_z)
    
    def set_position(self, x, y, z):
        """Записать координаты (БЕЗ проверок - быстро)"""
        if "char_base" not in self.cache:
            self._update()
        
        if "char_base" not in self.cache:
            return False
        
        char_base = self.cache["char_base"]
        
        # Записываем координаты
        self.memory.write_float(char_base + 0xA00, x)  # X
        self.memory.write_float(char_base + 0x9F8, y)  # Y
        self.memory.write_float(char_base + 0x9FC, z)  # Z
        
        return True
    
    def get_target_position(self):
        """Получить координаты таргета"""
        # Обновляем target_id
        self.target_id = resolve_offset(self.memory, OFFSETS["target_id"], self.cache)
        
        if not self.target_id or self.target_id == 0:
            return None
        
        # Получаем selection_origin
        selection_origin = resolve_offset(self.memory, OFFSETS["selection_origin"], self.cache)
        if selection_origin:
            self.cache["selection_origin"] = selection_origin
        
        # Получаем selection_ptr
        selection_ptr = resolve_offset(self.memory, OFFSETS["selection_ptr"], self.cache)
        if not selection_ptr:
            return None
        
        self.cache["selection_ptr"] = selection_ptr
        
        # Получаем target_ptr
        target_ptr = resolve_offset(self.memory, OFFSETS["target_ptr"], self.cache)
        if not target_ptr:
            return None
        
        self.cache["target_ptr"] = target_ptr
        
        # Читаем координаты
        x = resolve_offset(self.memory, OFFSETS["target_pos_x"], self.cache)
        y = resolve_offset(self.memory, OFFSETS["target_pos_y"], self.cache)
        z = resolve_offset(self.memory, OFFSETS["target_pos_z"], self.cache)
        
        if x is None or y is None or z is None:
            return None
        
        return (x, y, z)
    
    def refresh(self):
        """Обновить все данные"""
        self._update()
    
    def set_target_id(self, target_id):
        """Записать target_id (для Attack)"""
        if "char_base" not in self.cache:
            self._update()
        
        if "char_base" not in self.cache:
            return False
        
        char_base = self.cache["char_base"]
        return self.memory.write_uint(char_base + 0x7B4, target_id)
    
    def set_fly_speed_z(self, value):
        """Записать fly_speed_z (для Follow)"""
        if "char_base" not in self.cache:
            self._update()
        
        if "char_base" not in self.cache:
            return False
        
        char_base = self.cache["char_base"]
        return self.memory.write_float(char_base + 0x12A8, value)


class WorldManager:
    """Управление миром (лут, игроки, NPC)"""
    
    def __init__(self, memory):
        self.memory = memory
        self.cache = {}
        self._update_base()
    
    def _update_base(self):
        """Обновить базовые адреса"""
        world_origin = resolve_offset(self.memory, OFFSETS["world_origin"], self.cache)
        if world_origin:
            self.cache["world_origin"] = world_origin
        
        world_base = resolve_offset(self.memory, OFFSETS["world_base"], self.cache)
        if world_base:
            self.cache["world_base"] = world_base
    
    def has_any_loot(self):
        """
        БЫСТРАЯ проверка: есть ли вообще лут (БЕЗ фильтрации по расстоянию)
        
        Returns:
            bool: True если есть хотя бы один предмет лута
        """
        loot_count = resolve_offset(self.memory, OFFSETS["loot_count"], self.cache)
        return loot_count is not None and loot_count > 0
    
    def get_loot_nearby(self, char_position, max_distance):
        """
        Получить лут в радиусе от персонажа
        
        Args:
            char_position: (x, y, z) координаты персонажа
            max_distance: максимальное расстояние в метрах
        
        Returns:
            list: список предметов лута [{x, y}, ...]
        """
        import math
        
        loot_items = resolve_offset(self.memory, OFFSETS["loot_items"], self.cache)
        
        if not loot_items:
            return []
        
        char_x, char_y, char_z = char_position
        nearby = []
        
        for item in loot_items:
            item_x = item.get('x')
            item_y = item.get('y')
            
            if item_x is None or item_y is None:
                continue
            
            # Расстояние в 2D (игнорируем Z)
            distance = math.sqrt((item_x - char_x)**2 + (item_y - char_y)**2)
            
            if distance <= max_distance:
                nearby.append(item)
        
        return nearby