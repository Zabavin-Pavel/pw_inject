"""
Базовые классы для игровых структур
"""
import time

class GameStruct:
    """Базовый класс для работы с памятью"""
    
    def __init__(self, memory):
        self.mem = memory
    
    def _get_base_address(self):
        """Переопределяется в наследниках"""
        return 0
    
    def _read_int(self, offset):
        """Прочитать int"""
        base = self._get_base_address()
        if base == 0:
            return None
        return self.mem.read_int(base + offset)
    
    def _read_uint64(self, offset):
        """Прочитать uint64"""
        base = self._get_base_address()
        if base == 0:
            return None
        return self.mem.read_uint64(base + offset)
    
    def _read_float(self, offset):
        """Прочитать float"""
        base = self._get_base_address()
        if base == 0:
            return None
        return self.mem.read_float(base + offset)


class GameOriginal(GameStruct):
    """Структуры со статическим указателем"""
    
    def __init__(self, memory, static_offset, ptr_offset):
        super().__init__(memory)
        self.static_offset = static_offset
        self.ptr_offset = ptr_offset
        self._base_address = 0
        self._last_check_time = 0
        self.check_interval = 1.0
    
    def _calculate_base_address(self):
        """Вычислить базовый адрес"""
        ptr1 = self.mem.read_uint64(self.mem.module_base + self.static_offset)
        if ptr1 is None or ptr1 == 0:
            return 0
        
        base = self.mem.read_uint64(ptr1 + self.ptr_offset)
        if base is None:
            return 0
        
        return base
    
    def _get_base_address(self):
        """Получить базовый адрес с кешированием"""
        current_time = time.time()
        
        if current_time - self._last_check_time > self.check_interval:
            new_base = self._calculate_base_address()
            if new_base != self._base_address:
                self._base_address = new_base
            self._last_check_time = current_time
        
        return self._base_address
    
    def is_valid(self):
        """Проверка валидности"""
        return self._get_base_address() != 0


class WorldObject(GameStruct):
    """Объекты в игровом мире (лут, NPC, игроки)"""
    
    def __init__(self, memory, obj_ptr):
        super().__init__(memory)
        self.obj_ptr = obj_ptr
        self._data_ptr = None
        if obj_ptr:
            self._data_ptr = self.mem.read_uint64(obj_ptr + 0x10)
    
    def _get_base_address(self):
        return self._data_ptr if self._data_ptr else 0
    
    def is_valid(self):
        return self._data_ptr is not None and self._data_ptr != 0