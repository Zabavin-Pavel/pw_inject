"""
Структура персонажа игрока
"""
import ctypes
import logging
from constants import CLASS_NAMES_DEBUG
from game_structs.base import GameOriginal

class CharBase(GameOriginal):
    """Структура персонажа игрока"""
    
    OFFSET_STATIC_PTR = 0x13FAB08
    PTR_OFFSET = 0x68
    
    # Основные поля
    OFFSET_CHAR_ID = 0x6A8
    OFFSET_CHAR_NAME_PTR = 0x9C8
    OFFSET_CHAR_CLASS = 0x9D0
    OFFSET_TARGET_ID = 0x7B4
    OFFSET_LEVEL = 0x6B4
    # OFFSET_IS_LEADER = 0x???  # TODO: найти оффсет
    
    # HP/MP
    OFFSET_HP = 0x6BC
    OFFSET_MAX_HP = 0x730
    OFFSET_MP = 0x6C0
    OFFSET_MAX_MP = 0x734
    
    # Координаты
    OFFSET_X = 0xA00
    OFFSET_Y = 0x9F8
    OFFSET_Z = 0x9FC
    
    # Характеристики
    OFFSET_VITALITY = 0x720
    OFFSET_MAGIC = 0x724
    OFFSET_STRENGTH = 0x728
    OFFSET_DEXTERITY = 0x72C
    
    def __init__(self, memory):
        super().__init__(memory, self.OFFSET_STATIC_PTR, self.PTR_OFFSET)
    
    def is_valid(self):
        """Проверить что CharBase валиден"""
        if self._base_address == 0:
            return False
        
        char_id = self._read_int(self.OFFSET_CHAR_ID)
        if char_id is None or char_id == 0:
            return False
        
        return True
    
    @property
    def char_id(self):
        """ID персонажа"""
        value = self._read_int(self.OFFSET_CHAR_ID)
        return value if value is not None else 0
    
    @property
    def char_class(self):
        """Класс персонажа (0-9)"""
        value = self._read_int(self.OFFSET_CHAR_CLASS)
        return value if value is not None else None
    
    @property
    def char_class_name(self):
        """Название класса"""
        char_class = self.char_class
        if char_class is None:
            return "Unknown"
        return CLASS_NAMES_DEBUG.get(char_class, f"Class_{char_class}")
    
    @property
    def target_id(self):
        """ID текущей цели"""
        value = self._read_int(self.OFFSET_TARGET_ID)
        return value if value is not None else 0
    
    @property
    def level(self):
        """Уровень"""
        value = self._read_int(self.OFFSET_LEVEL)
        return value if value is not None else 0
    
    @property
    def hp(self):
        """Текущее HP"""
        value = self._read_int(self.OFFSET_HP)
        return value if value is not None else 0
    
    @property
    def max_hp(self):
        """Максимальное HP"""
        value = self._read_int(self.OFFSET_MAX_HP)
        return value if value is not None else 0
    
    @property
    def mp(self):
        """Текущая мана"""
        value = self._read_int(self.OFFSET_MP)
        return value if value is not None else 0
    
    @property
    def max_mp(self):
        """Максимальная мана"""
        value = self._read_int(self.OFFSET_MAX_MP)
        return value if value is not None else 0
    
    @property
    def x(self):
        """Координата X"""
        value = self._read_float(self.OFFSET_X)
        return value if value is not None else 0.0
    
    @property
    def y(self):
        """Координата Y"""
        value = self._read_float(self.OFFSET_Y)
        return value if value is not None else 0.0
    
    @property
    def z(self):
        """Координата Z"""
        value = self._read_float(self.OFFSET_Z)
        return value if value is not None else 0.0
    
    @property
    def position(self):
        """Позиция (x, y, z)"""
        return (self.x, self.y, self.z)
    
    @property
    def vitality(self):
        """Живучесть"""
        value = self._read_int(self.OFFSET_VITALITY)
        return value if value is not None else 0
    
    @property
    def magic(self):
        """Магия"""
        value = self._read_int(self.OFFSET_MAGIC)
        return value if value is not None else 0
    
    @property
    def strength(self):
        """Сила"""
        value = self._read_int(self.OFFSET_STRENGTH)
        return value if value is not None else 0
    
    @property
    def dexterity(self):
        """Ловкость"""
        value = self._read_int(self.OFFSET_DEXTERITY)
        return value if value is not None else 0
    
    @property
    def hp_percent(self):
        """Процент HP (0.0 - 1.0)"""
        max_hp = self.max_hp
        if max_hp == 0:
            return 0.0
        return self.hp / max_hp
    
    @property
    def mp_percent(self):
        """Процент маны (0.0 - 1.0)"""
        max_mp = self.max_mp
        if max_mp == 0:
            return 0.0
        return self.mp / max_mp
    
    @property
    def is_leader(self):
        """Является ли персонаж лидером группы"""
        # TODO: когда найдёшь оффсет, раскомментируй:
        # value = self._read_int(self.OFFSET_IS_LEADER)
        # return value == 1 if value is not None else False
        return False  # Пока всегда False
    
    @property
    def char_name(self):
        """Имя персонажа"""
        ptr = self.mem.read_uint64(self._base_address + self.OFFSET_CHAR_NAME_PTR)
        if ptr is None or ptr == 0:
            return f"Char_{self.char_id}"
        
        buffer = (ctypes.c_wchar * 30)()
        bytes_read = ctypes.c_size_t()
        
        result = self.mem.kernel32.ReadProcessMemory(
            self.mem.process_handle,
            ctypes.c_void_p(ptr),
            buffer,
            60,
            ctypes.byref(bytes_read)
        )
        
        if result:
            try:
                name = ''.join(buffer).split('\x00')[0]
                return name[:20] if name else f"Char_{self.char_id}"
            except:
                return f"Char_{self.char_id}"
        
        return f"Char_{self.char_id}"