"""
Менеджер окружающего мира
"""
import logging
from game_structs.base import GameOriginal

class WorldManager(GameOriginal):
    """Менеджер окружающего мира"""
    
    OFFSET_STATIC_PTR = 0x148C338
    PTR_OFFSET = 0x10
    
    # НОВЫЕ оффсеты на основе анализа
    OFFSET_LOOT_CONTAINER = 0x28  # Указатель на контейнер лута
    OFFSET_PLAYERS_ARRAY = 0x30
    
    def __init__(self, memory):
        super().__init__(memory, self.OFFSET_STATIC_PTR, self.PTR_OFFSET)
        logging.info(f"WorldManager создан для PID {memory.pid}")
    
    def get_loot_ids(self):
        """Получить ID лута - ОТЛАДОЧНАЯ ВЕРСИЯ"""
        base = self._get_base_address()
        if base == 0:
            logging.error("WorldManager: base = 0")
            return []
        
        # Шаг 1: Читаем указатель на КОНТЕЙНЕР лута
        loot_container_ptr = self.mem.read_uint64(base + self.OFFSET_LOOT_CONTAINER)
        if not loot_container_ptr:
            logging.error(f"loot_container_ptr = NULL")
            return []
        
        logging.info(f"=== ОТЛАДКА ЛУТА ===")
        logging.info(f"base = {hex(base)}")
        logging.info(f"loot_container = {hex(loot_container_ptr)}")
        
        # Шаг 2: Читаем СЧЁТЧИК (offset 0x18)
        loot_count = self.mem.read_int(loot_container_ptr + 0x18)
        logging.info(f"loot_count [+0x18] = {loot_count}")
        
        # Шаг 3: Пробуем разные варианты чтения массива
        logging.info(f"\n--- Вариант 1: Массив начинается с +0x28 ---")
        self._try_read_loot_array(loot_container_ptr, 0x28, loot_count)
        
        logging.info(f"\n--- Вариант 2: Массив начинается с +0x30 ---")
        self._try_read_loot_array(loot_container_ptr, 0x30, loot_count)
        
        logging.info(f"\n--- Вариант 3: Прямое чтение с offset 0x48, 0x50, 0x58... ---")
        for test_offset in [0x48, 0x50, 0x58, 0x60, 0x68, 0x70]:
            ptr = self.mem.read_uint64(loot_container_ptr + test_offset)
            if ptr and ptr != 0:
                logging.info(f"  [{hex(test_offset)}] = {hex(ptr)}")
                # Пробуем читать ID
                id_v1 = self.mem.read_int(ptr + 0x140)
                logging.info(f"    [+0x140] ID = {id_v1} ({hex(id_v1) if id_v1 else 'NULL'})")
        
        return []  # Пока ничего не возвращаем, только отладка
    
    def _try_read_loot_array(self, container_ptr, array_offset, expected_count):
        """Попробовать прочитать массив с заданного оффсета"""
        # Читаем указатель на начало массива
        array_ptr = self.mem.read_uint64(container_ptr + array_offset)
        
        if not array_ptr:
            logging.info(f"  array_ptr [{hex(array_offset)}] = NULL")
            return
        
        logging.info(f"  array_ptr [{hex(array_offset)}] = {hex(array_ptr)}")
        
        # Пробуем прочитать первые N элементов (шаг 8 байт)
        found = 0
        for i in range(min(expected_count + 5, 20)):  # Читаем чуть больше чем count
            offset = i * 8
            
            # Читаем указатель
            item_ptr = self.mem.read_uint64(array_ptr + offset)
            
            if not item_ptr or item_ptr == 0:
                logging.info(f"    [{i}] offset={hex(offset)}: NULL")
                continue
            
            # Пробуем прочитать ID
            loot_id = self.mem.read_int(item_ptr + 0x140)
            
            logging.info(f"    [{i}] offset={hex(offset)}: ptr={hex(item_ptr)}, ID={loot_id} ({hex(loot_id) if loot_id else 'NULL'})")
            
            if loot_id and 0 < loot_id < 0x7FFFFFFF:
                found += 1
        
        logging.info(f"  Найдено валидных ID: {found}")
    
    def get_nearby_player_ids(self):
        """Игроки - пока заглушка"""
        return []
    
    def get_npc_ids(self):
        return []