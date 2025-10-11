"""
Игровые структуры v2 с централизованным менеджментом памяти
"""

import time
import logging
from typing import Optional, Dict, List, Tuple, Any
from dataclasses import dataclass
from game_structs.offsets import CHAR_BASE, WORLD_MANAGER, GAME_INFO

# ============================================
# МЕНЕДЖЕР ПАМЯТИ
# ============================================

@dataclass 
class CachedAddress:
    """Закешированный адрес с метаданными"""
    address: int
    path: str
    timestamp: float

class GameMemoryManager:
    """
    Централизованный менеджер памяти для одного процесса игры
    Кеширует все базовые адреса и управляет чтением/записью
    """
    
    def __init__(self, memory, pid: int):
        self.memory = memory
        self.pid = pid
        
        # Кеш базовых адресов структур
        self._base_cache: Dict[str, CachedAddress] = {}
        
        # Кеш адресов массивов
        self._array_cache: Dict[str, CachedAddress] = {}
        
        # Постоянные данные (не меняются за сессию)
        self._permanent_data: Dict[str, Any] = {}
        
        # Логгер
        self.logger = logging.getLogger(f"GameMemory[PID:{pid}]")
        
        # Флаг валидности
        self._is_valid = False
        
        # Инициализация
        self._initialize()
    
    def _initialize(self):
        """Инициализировать все базовые адреса"""
        # CharBase
        char_base = self._resolve_pointer_chain(
            CHAR_BASE["static_path"],
            "CharBase"
        )
        
        if char_base:
            self._base_cache["char_base"] = CachedAddress(
                address=char_base,
                path=self._format_path(CHAR_BASE["static_path"], char_base),
                timestamp=time.time()
            )
            self._is_valid = True
            
            # Читаем постоянные данные
            self._read_permanent_data(char_base)
            
            # Кешируем адрес массива группы
            self._cache_party_array(char_base)
        
        # WorldManager
        world_base = self._resolve_pointer_chain(
            WORLD_MANAGER["static_path"],
            "WorldManager"
        )
        
        if world_base:
            self._base_cache["world_base"] = CachedAddress(
                address=world_base,
                path=self._format_path(WORLD_MANAGER["static_path"], world_base),
                timestamp=time.time()
            )
            
            # Кешируем адреса массивов
            self._cache_world_arrays(world_base)
    
    def _resolve_pointer_chain(self, path: List, name: str) -> Optional[int]:
        """Пройти по цепочке указателей и вернуть финальный адрес"""
        try:
            current = None
            
            # Первый элемент - статический указатель
            if isinstance(path[0], str) and "+" in path[0]:
                parts = path[0].split("+")
                offset = int(parts[1], 16)
                current = self.memory.read_uint64(self.memory.module_base + offset)
                
                if not current:
                    self.logger.warning(f"{name}: Failed to read static pointer")
                    return None
            
            # Проходим по цепочке
            for offset in path[1:]:
                if current is None:
                    break
                current = self.memory.read_uint64(current + offset)
                if not current:
                    self.logger.warning(f"{name}: Chain broken at offset {hex(offset)}")
                    return None
            
            return current
            
        except Exception as e:
            self.logger.error(f"{name}: Failed to resolve chain: {e}")
            return None
    
    def _format_path(self, path: List, result: int) -> str:
        """Форматировать путь для логирования"""
        path_str = f"{path[0]}"
        for offset in path[1:]:
            path_str += f" -> +{hex(offset)}"
        path_str += f" = {hex(result)}"
        return path_str
    
    def _read_permanent_data(self, char_base: int):
        """Прочитать неизменяемые данные персонажа"""
        # ID персонажа
        char_id = self.memory.read_int(char_base + CHAR_BASE["fields"]["char_id"])
        if char_id:
            self._permanent_data["char_id"] = char_id
        
        # Класс персонажа
        char_class = self.memory.read_int(char_base + CHAR_BASE["fields"]["char_class"])
        if char_class is not None:
            self._permanent_data["char_class"] = char_class
        
        # Имя персонажа
        name_ptr = self.memory.read_uint64(char_base + CHAR_BASE["fields"]["char_name_ptr"])
        if name_ptr:
            name = self.memory.read_string(name_ptr, max_length=30)
            if name:
                self._permanent_data["char_name"] = name
            else:
                self._permanent_data["char_name"] = f"Char_{char_id}"
        
        # Обновляем логгер с именем персонажа
        name = self._permanent_data.get("char_name", "Unknown")
        char_class = self._permanent_data.get("char_class", "?")
        self.logger = logging.getLogger(f"GameMemory[{name}(Class:{char_class}) PID:{self.pid}]")
    
    def _cache_party_array(self, char_base: int):
        """Закешировать адрес массива группы"""
        party_base = self.memory.read_uint64(
            char_base + CHAR_BASE["party"]["base_offset"]
        )
        if party_base:
            array_addr = self.memory.read_uint64(
                party_base + CHAR_BASE["party"]["array_offset"]
            )
            if array_addr:
                self._array_cache["party_array"] = CachedAddress(
                    address=array_addr,
                    path=f"CharBase+{hex(CHAR_BASE['party']['base_offset'])}->+{hex(CHAR_BASE['party']['array_offset'])}",
                    timestamp=time.time()
                )
    
    def _cache_world_arrays(self, world_base: int):
        """Закешировать адреса массивов WorldManager"""
        # Массив лута
        loot_container = self.memory.read_uint64(
            world_base + WORLD_MANAGER["loot"]["container_path"][0]
        )
        if loot_container:
            loot_array = self.memory.read_uint64(
                loot_container + WORLD_MANAGER["loot"]["array_offset"]
            )
            if loot_array:
                self._array_cache["loot_array"] = CachedAddress(
                    address=loot_array,
                    path=f"WorldBase->loot_array",
                    timestamp=time.time()
                )
        
        # Массив игроков
        people_container = self.memory.read_uint64(
            world_base + WORLD_MANAGER["people"]["container_path"][0]
        )
        if people_container:
            people_array = self.memory.read_uint64(
                people_container + WORLD_MANAGER["people"]["array_offset"]
            )
            if people_array:
                self._array_cache["people_array"] = CachedAddress(
                    address=people_array,
                    path=f"WorldBase->people_array",
                    timestamp=time.time()
                )
    
    def get_base(self, key: str) -> Optional[int]:
        """Получить базовый адрес из кеша"""
        if key in self._base_cache:
            return self._base_cache[key].address
        return None
    
    def get_array(self, key: str) -> Optional[int]:
        """Получить адрес массива из кеша"""
        if key in self._array_cache:
            return self._array_cache[key].address
        return None
    
    def get_permanent(self, key: str) -> Any:
        """Получить постоянные данные"""
        return self._permanent_data.get(key)
    
    def is_valid(self) -> bool:
        """Проверка валидности через CharBase"""
        if not self._is_valid:
            return False
        
        # Быстрая проверка что CharBase всё ещё валиден
        char_base = self.get_base("char_base")
        if not char_base:
            return False
        
        # Проверяем ID персонажа
        char_id = self.memory.read_int(
            char_base + CHAR_BASE["fields"]["char_id"]
        )
        return char_id is not None and char_id > 0

# ============================================
# ИГРОВЫЕ СТРУКТУРЫ
# ============================================

class GameCharacter:
    """Структура персонажа"""
    
    def __init__(self, manager: GameMemoryManager):
        self.manager = manager
        self.offsets = CHAR_BASE["fields"]
    
    @property
    def base(self) -> Optional[int]:
        return self.manager.get_base("char_base")
    
    @property
    def char_id(self) -> int:
        """ID персонажа из кеша"""
        return self.manager.get_permanent("char_id") or 0
    
    @property
    def char_name(self) -> str:
        """Имя персонажа из кеша"""
        return self.manager.get_permanent("char_name") or "Unknown"
    
    @property
    def char_class(self) -> int:
        """Класс персонажа из кеша"""
        return self.manager.get_permanent("char_class") or -1
    
    @property
    def level(self) -> int:
        base = self.base
        if base:
            return self.manager.memory.read_int(base + self.offsets["level"]) or 0
        return 0
    
    @property
    def hp(self) -> int:
        base = self.base
        if base:
            return self.manager.memory.read_int(base + self.offsets["hp"]) or 0
        return 0
    
    @property
    def mp(self) -> int:
        base = self.base
        if base:
            return self.manager.memory.read_int(base + self.offsets["mp"]) or 0
        return 0
    
    @property
    def target_id(self) -> int:
        base = self.base
        if base:
            return self.manager.memory.read_int(base + self.offsets["target_id"]) or 0
        return 0
    
    @property
    def position(self) -> Tuple[float, float, float]:
        base = self.base
        if base:
            x = self.manager.memory.read_float(base + self.offsets["x"]) or 0.0
            y = self.manager.memory.read_float(base + self.offsets["y"]) or 0.0
            z = self.manager.memory.read_float(base + self.offsets["z"]) or 0.0
            return (x, y, z)
        return (0.0, 0.0, 0.0)
    
    def get_party_members(self) -> List[int]:
        """Получить ID членов группы"""
        base = self.base
        if not base:
            return []
        
        # Используем кешированный адрес массива
        array_addr = self.manager.get_array("party_array")
        if not array_addr:
            return []
        
        # Читаем счетчик
        party_base = self.manager.memory.read_uint64(
            base + CHAR_BASE["party"]["base_offset"]
        )
        if not party_base:
            return []
        
        count = self.manager.memory.read_int(
            party_base + CHAR_BASE["party"]["count_offset"]
        ) or 0
        
        if count == 0:
            return []
        
        # Читаем ID членов группы
        members = []
        max_members = CHAR_BASE["party"]["max_members"]
        
        for i in range(min(count, max_members)):
            member_ptr = self.manager.memory.read_uint64(array_addr + i * 8)
            if member_ptr:
                member_id = self.manager.memory.read_int(
                    member_ptr + CHAR_BASE["party"]["member_id_offset"]
                )
                if member_id:
                    members.append(member_id)
        
        return members

class GameWorld:
    """Структура окружающего мира"""
    
    def __init__(self, manager: GameMemoryManager):
        self.manager = manager
    
    @property
    def base(self) -> Optional[int]:
        return self.manager.get_base("world_base")
    
    def get_loot_positions(self) -> List[Tuple[float, float]]:
        """Получить координаты лута"""
        # Используем кешированный адрес массива
        array_addr = self.manager.get_array("loot_array")
        if not array_addr:
            return []
        
        items = []
        max_iter = WORLD_MANAGER["loot"]["max_iterate"]
        step = WORLD_MANAGER["loot"]["step"]
        
        for offset in range(0, max_iter, step):
            item_ptr = self.manager.memory.read_uint64(array_addr + offset)
            if not item_ptr:
                continue
            
            data_ptr = self.manager.memory.read_uint64(
                item_ptr + WORLD_MANAGER["loot"]["item_data_offset"]
            )
            if data_ptr:
                x = self.manager.memory.read_float(
                    data_ptr + WORLD_MANAGER["loot"]["x_offset"]
                )
                y = self.manager.memory.read_float(
                    data_ptr + WORLD_MANAGER["loot"]["y_offset"]
                )
                if x and y:
                    items.append((x, y))
        
        return items
    
    def get_nearby_player_ids(self) -> List[int]:
        """Получить ID окружающих игроков"""
        # Используем кешированный адрес массива
        array_addr = self.manager.get_array("people_array")
        if not array_addr:
            return []
        
        players = []
        max_iter = WORLD_MANAGER["people"]["max_iterate"]
        step = WORLD_MANAGER["people"]["step"]
        
        found = 0
        for offset in range(0, max_iter, step):
            if found >= 100:  # Ограничение
                break
            
            person_ptr = self.manager.memory.read_uint64(array_addr + offset)
            if not person_ptr:
                continue
            
            data_ptr = self.manager.memory.read_uint64(
                person_ptr + WORLD_MANAGER["people"]["person_data_offset"]
            )
            if data_ptr:
                player_id = self.manager.memory.read_int(
                    data_ptr + WORLD_MANAGER["people"]["id_offset"]
                )
                if player_id and player_id > 0:
                    players.append(player_id)
                    found += 1
        
        return players
    
    def get_npc_count(self) -> int:
        """Получить количество NPC"""
        # Статический адрес
        parts = WORLD_MANAGER["npc"]["static_count"].split("+")
        offset = int(parts[1], 16)
        count_addr = self.manager.memory.module_base + offset
        return self.manager.memory.read_int(count_addr) or 0

class GameInfo:
    """Общая игровая информация"""
    
    def __init__(self, manager: GameMemoryManager):
        self.manager = manager
    
    @property
    def location_id(self) -> int:
        """ID локации"""
        result = self.manager._resolve_pointer_chain(
            GAME_INFO["location"]["static_path"],
            "Location"
        )
        return result if result else 0
    
    @property
    def teleport_id(self) -> int:
        """ID руны телепорта"""
        result = self.manager._resolve_pointer_