"""
Игровые структуры для чтения/записи данных из памяти
"""
from offsets import OFFSETS, resolve_offset


class CharBase:
    """Базовая информация о персонаже"""
    
    def __init__(self, memory):
        self.memory = memory
        self.cache = {}
        self._update()
    
    def _update(self):
        """Обновить данные из памяти"""
        # Получаем базовые адреса
        char_origin = resolve_offset(self.memory, OFFSETS["char_origin"], self.cache)
        if char_origin:
            self.cache["char_origin"] = char_origin
        
        char_base = resolve_offset(self.memory, OFFSETS["char_base"], self.cache)
        if char_base:
            self.cache["char_base"] = char_base
        
        # Читаем данные
        self.char_id = resolve_offset(self.memory, OFFSETS["char_id"], self.cache)
        self.char_class = resolve_offset(self.memory, OFFSETS["char_class"], self.cache)
        self.char_name = resolve_offset(self.memory, OFFSETS["char_name"], self.cache)
        self.char_level = resolve_offset(self.memory, OFFSETS["char_level"], self.cache)
        self.char_target_id = resolve_offset(self.memory, OFFSETS["char_target_id"], self.cache)
        
        # HP/MP
        self.char_hp = resolve_offset(self.memory, OFFSETS["char_hp"], self.cache)
        self.char_max_hp = resolve_offset(self.memory, OFFSETS["char_max_hp"], self.cache)
        
        # Координаты
        self.char_pos_x = resolve_offset(self.memory, OFFSETS["char_pos_x"], self.cache)
        self.char_pos_y = resolve_offset(self.memory, OFFSETS["char_pos_y"], self.cache)
        self.char_pos_z = resolve_offset(self.memory, OFFSETS["char_pos_z"], self.cache)
    
    def is_valid(self):
        """Проверка валидности данных"""
        return self.char_id is not None and self.char_id != 0
    
    def get_position(self):
        """Получить координаты (x, y, z)"""
        self._update()
        return (self.char_pos_x, self.char_pos_y, self.char_pos_z)
    
    def set_position(self, x, y, z):
        """Записать координаты в память"""
        if "char_base" not in self.cache:
            self._update()
        
        if "char_base" not in self.cache:
            return False
        
        char_base = self.cache["char_base"]
        
        # Записываем координаты
        success = True
        success &= self.memory.write_float(char_base + 0xA00, x)  # X
        success &= self.memory.write_float(char_base + 0x9F8, y)  # Y
        success &= self.memory.write_float(char_base + 0x9FC, z)  # Z
        
        return success
    
    def get_target_position(self):
        """Получить координаты таргета"""
        # Обновляем target_id
        self.char_target_id = resolve_offset(self.memory, OFFSETS["char_target_id"], self.cache)
        
        if not self.char_target_id or self.char_target_id == 0:
            return None
        
        # Получаем target_origin
        target_origin = resolve_offset(self.memory, OFFSETS["target_origin"], self.cache)
        if target_origin:
            self.cache["target_origin"] = target_origin
        
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
    
    def get_loot_nearby(self, char_position, max_distance=50):
        """Получить лут вокруг персонажа"""
        char_x, char_y, _ = char_position
        
        # Получаем контейнер
        loot_container = resolve_offset(self.memory, OFFSETS["loot_container"], self.cache)
        if loot_container:
            self.cache["loot_container"] = loot_container
        
        # Получаем все предметы
        loot_items_raw = resolve_offset(self.memory, OFFSETS["loot_items"], self.cache)
        
        # Фильтруем по расстоянию
        loot_items = []
        if loot_items_raw:
            for item in loot_items_raw:
                loot_x = item.get('x')
                loot_y = item.get('y')
                
                if loot_x is not None and loot_y is not None:
                    dx = abs(loot_x - char_x)
                    dy = abs(loot_y - char_y)
                    
                    if dx <= max_distance and dy <= max_distance:
                        loot_items.append(item)
        
        return loot_items
    
    def get_people_nearby(self, char_position=None, max_distance=None):
        """Получить людей вокруг"""
        # Получаем контейнер
        people_container = resolve_offset(self.memory, OFFSETS["people_container"], self.cache)
        if people_container:
            self.cache["people_container"] = people_container
        
        # Получаем всех людей
        people_items_raw = resolve_offset(self.memory, OFFSETS["people_items"], self.cache)
        
        # Фильтруем
        people_items = []
        if people_items_raw:
            for item in people_items_raw:
                people_id = item.get('id')
                if people_id is not None and people_id > 1:
                    people_items.append(item)
        
        return people_items