"""
Игровые структуры - обёртки над оффсетами
"""
from offsets import OFFSETS, resolve_offset


class CharBase:
    """Обёртка над персонажем"""
    
    def __init__(self, memory):
        self.memory = memory
        self._cache = {}
        
    def _get(self, key):
        """Получить значение оффсета с кешированием базовых адресов"""
        return resolve_offset(self.memory, OFFSETS[key], self._cache)
    
    def _get_address(self, key):
        """Получить адрес оффсета (для записи)"""
        # Получаем путь
        path_str = OFFSETS[key]
        parts = path_str.split()
        
        # Парсим тип и базу
        type_and_ref = parts[0].split(":", 1)
        data_type = type_and_ref[0]
        ref = type_and_ref[1] if len(type_and_ref) > 1 else None
        
        # Получаем базовый адрес
        if ref and ref in self._cache:
            current_addr = self._cache[ref]
        elif ref and ref in OFFSETS:
            current_addr = resolve_offset(self.memory, OFFSETS[ref], self._cache)
        else:
            return None
        
        # Применяем оффсеты
        i = 1
        while i < len(parts):
            part = parts[i]
            
            if part.startswith("+0x"):
                offset = int(part[1:], 16)
                current_addr += offset
                
                # Если следующий элемент "->" - читаем указатель
                if i + 1 < len(parts) and parts[i + 1] == "->":
                    current_addr = self.memory.read_uint64(current_addr)
                    if not current_addr:
                        return None
                    i += 1
            
            i += 1
        
        return current_addr
    
    @property
    def char_id(self):
        return self._get("char_id")
    
    @property
    def char_class(self):
        return self._get("char_class")
    
    @property
    def char_name(self):
        return self._get("char_name")
    
    @property
    def char_level(self):
        return self._get("char_level")
    
    @property
    def target_id(self):
        return self._get("char_target_id")
    
    @property
    def hp(self):
        return self._get("char_hp")
    
    @property
    def max_hp(self):
        return self._get("char_max_hp")
    
    @property
    def pos_x(self):
        return self._get("char_pos_x")
    
    @property
    def pos_y(self):
        return self._get("char_pos_y")
    
    @property
    def pos_z(self):
        return self._get("char_pos_z")
    
    @property
    def position(self):
        """Возвращает tuple (x, y, z)"""
        return (self.pos_x, self.pos_y, self.pos_z)
    
    def set_position(self, x, y, z):
        """Записать новые координаты"""
        addr_x = self._get_address("char_pos_x")
        addr_y = self._get_address("char_pos_y")
        addr_z = self._get_address("char_pos_z")
        
        if addr_x and addr_y and addr_z:
            self.memory.write_float(addr_x, x)
            self.memory.write_float(addr_y, y)
            self.memory.write_float(addr_z, z)
            return True
        return False
    
    # Party
    @property
    def party_ptr(self):
        return self._get("party_ptr")
    
    @property
    def in_party(self):
        """Проверка что персонаж в группе"""
        return self.party_ptr is not None and self.party_ptr != 0
    
    @property
    def party_count(self):
        if not self.in_party:
            return 0
        return self._get("party_count")
    
    @property
    def party_leader_id(self):
        if not self.in_party:
            return None
        return self._get("party_leader_id")
    
    @property
    def is_leader(self):
        """Проверка что персонаж - лидер группы"""
        if not self.in_party:
            return False
        return self.party_leader_id == self.char_id
    
    @property
    def party_members(self):
        """Получить список ID участников группы"""
        if not self.in_party:
            return []
        members = self._get("party_members")
        if members:
            return [m['id'] for m in members if m['id'] != 0]
        return []
    
    def is_valid(self):
        """Проверка валидности структуры"""
        char_id = self.char_id
        return char_id is not None and char_id != 0


class WorldManager:
    """Обёртка над World Manager"""
    
    def __init__(self, memory):
        self.memory = memory
        self._cache = {}
    
    def _get(self, key):
        """Получить значение оффсета с кешированием"""
        return resolve_offset(self.memory, OFFSETS[key], self._cache)
    
    @property
    def loot_count(self):
        return self._get("loot_count")
    
    @property
    def loot_container(self):
        return self._get("loot_container")
    
    def get_nearby_loot(self, char_x, char_y, radius=50):
        """
        Получить лут вокруг позиции персонажа
        Args:
            char_x, char_y: координаты персонажа
            radius: радиус поиска
        """
        loot_items_raw = self._get("loot_items")
        if not loot_items_raw:
            return []
        
        loot_items = []
        for item in loot_items_raw:
            loot_x = item.get('x')
            loot_y = item.get('y')
            
            if loot_x is not None and loot_y is not None:
                dx = abs(loot_x - char_x)
                dy = abs(loot_y - char_y)
                
                if dx <= radius and dy <= radius:
                    loot_items.append(item)
        
        return loot_items
    
    def is_valid(self):
        """Проверка валидности структуры"""
        container = self.loot_container
        return container is not None and container != 0


class GameInfo:
    """Обёртка над игровой информацией"""
    
    def __init__(self, memory):
        self.memory = memory
        self._cache = {}
    
    def _get(self, key):
        """Получить значение оффсета с кешированием"""
        return resolve_offset(self.memory, OFFSETS[key], self._cache)
    
    @property
    def location_id(self):
        return self._get("location_id")
    
    @property
    def teleport_id(self):
        return self._get("teleport_id")