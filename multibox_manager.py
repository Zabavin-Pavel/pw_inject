"""
Управление несколькими игровыми процессами - ОПТИМИЗИРОВАНО
"""
import ctypes
import logging
import math
from win32_api import TH32CS_SNAPPROCESS, PROCESSENTRY32
from memory import Memory
from game_structs import CharBase, WorldManager
from character import Character
from constants import DUNGEON_POINTS, LOOT_CHECK_RADIUS


class MultiboxManager:
    """Управление группой персонажей"""
    
    def __init__(self):
        self.characters = {}  # {pid: Character}
        self.kernel32 = ctypes.windll.kernel32
        
        # WorldManager для первого процесса (главный)
        self.world_manager = None
        self._main_pid = None
        
        # Зависимости (устанавливаются из GUI)
        self.ahk_manager = None
        self.app_state = None
    
    def set_ahk_manager(self, ahk_manager):
        """Установить AHK менеджер"""
        self.ahk_manager = ahk_manager
    
    def set_app_state(self, app_state):
        """Установить app_state"""
        self.app_state = app_state
    
    def _get_all_pids(self, process_name="ElementClient.exe"):
        """Получить список всех PID процесса"""
        snapshot = self.kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
        pe32 = PROCESSENTRY32()
        pe32.dwSize = ctypes.sizeof(PROCESSENTRY32)
        
        pids = []
        
        if self.kernel32.Process32First(snapshot, ctypes.byref(pe32)):
            while True:
                current_name = pe32.szExeFile.decode('utf-8', errors='ignore')
                if current_name.lower() == process_name.lower():
                    pids.append(pe32.th32ProcessID)
                
                if not self.kernel32.Process32Next(snapshot, ctypes.byref(pe32)):
                    break
        
        self.kernel32.CloseHandle(snapshot)
        return pids
    
    def validate_all(self):
        """Быстрая проверка валидности всех персонажей"""
        to_remove = []
        
        for pid, char in self.characters.items():
            if not char.is_valid():
                char.memory.close()
                to_remove.append(pid)
        
        for pid in to_remove:
            del self.characters[pid]
    
    def refresh(self):
        """Полное обновление списка персонажей"""
        current_pids = set(self._get_all_pids())
        existing_pids = set(self.characters.keys())
        
        # Удаляем закрытые процессы
        for pid in existing_pids - current_pids:
            char = self.characters[pid]
            char.memory.close()
            del self.characters[pid]
            
            # Если это был главный - сбрасываем WorldManager
            if pid == self._main_pid:
                self.world_manager = None
                self._main_pid = None
        
        # Проверяем существующие персонажи
        to_recreate = []
        for pid, char in self.characters.items():
            if not char.char_base.is_valid():
                to_recreate.append(pid)
        
        # Пересоздаём невалидные
        for pid in to_recreate:
            pass
        
        # Добавляем новые процессы
        for pid in current_pids - existing_pids:
            mem = Memory()
            if mem.attach_by_pid(pid):
                char_base = CharBase(mem)
                char = Character(pid, mem, char_base)
                self.characters[pid] = char
                
                # Первый процесс становится главным (для WorldManager)
                if self._main_pid is None:
                    self._main_pid = pid
                    self.world_manager = WorldManager(mem)
    
    def refresh_characters(self):
        """Алиас для refresh()"""
        self.refresh()
    
    def get_all_characters(self):
        """Получить список всех ВАЛИДНЫХ персонажей"""
        valid_chars = []
        for char in self.characters.values():
            if char.is_valid():
                valid_chars.append(char)
        return valid_chars
    
    def get_valid_characters(self):
        """Алиас для совместимости с GUI"""
        return self.get_all_characters()
    
    # ===================================================
    # LEADER AND GROUP
    # ===================================================

    def get_leader_and_group(self):
        """
        Найти группу с максимальным числом наших персонажей
        
        Returns:
            (leader: Character, members: list[Character]) или (None, [])
        """
        from offsets import resolve_offset, OFFSETS
        
        groups = {}  # {leader_id: [char1, char2, ...]}
        
        for char in self.get_all_characters():
            char.char_base.refresh()
            
            party_ptr = resolve_offset(char.memory, OFFSETS["party_ptr"], char.char_base.cache)
            
            if not party_ptr or party_ptr == 0:
                continue
            
            char.char_base.cache["party_ptr"] = party_ptr
            
            party_leader_id = resolve_offset(char.memory, OFFSETS["party_leader_id"], char.char_base.cache)
            
            if not party_leader_id:
                continue
            
            if party_leader_id not in groups:
                groups[party_leader_id] = []
            
            groups[party_leader_id].append(char)
        
        if not groups:
            return None, []
        
        # Самая большая группа
        largest_group_leader_id = max(groups.keys(), key=lambda lid: len(groups[lid]))
        largest_group = groups[largest_group_leader_id]
        
        # Находим лидера среди наших персонажей
        leader = None
        for char in largest_group:
            if char.char_base.char_id == largest_group_leader_id:
                leader = char
                break
        
        if not leader:
            return None, []
        
        return leader, largest_group

    # ===================================================
    # ТИПОВЫЕ ФУНКЦИИ ТЕЛЕПОРТАЦИИ (ОПТИМИЗИРОВАНО)
    # ===================================================
    
    def teleport_character(self, character, target_x, target_y, target_z, send_space=False):
        """
        Телепортировать одного персонажа (БЫСТРО, БЕЗ ПРОВЕРОК)
        
        Args:
            character: персонаж для телепорта
            target_x, target_y, target_z: целевые координаты
            send_space: нужно ли нажать space после телепорта
        
        Returns:
            bool: успех записи координат
        """
        if not character or not character.is_valid():
            return False
        
        # Записываем координаты
        success = character.char_base.set_position(target_x, target_y, target_z)
        
        if not success:
            return False
        
        # Нажимаем space если нужно
        if send_space and self.ahk_manager:
            self.ahk_manager.send_key_to_pid("space", character.pid)
        
        return True
    
    def teleport_group(self, characters, target_x, target_y, target_z):
        """
        Телепортировать группу персонажей (БЫСТРО, space для всех)
        
        Args:
            characters: список персонажей
            target_x, target_y, target_z: целевые координаты
        
        Returns:
            int: количество успешных телепортов
        """
        if not characters:
            return 0
        
        success_count = 0
        
        # Записываем координаты всем
        for char in characters:
            if char.is_valid():
                if char.char_base.set_position(target_x, target_y, target_z):
                    success_count += 1
        
        # Нажимаем space ВСЕМ СРАЗУ
        if success_count > 0 and self.ahk_manager:
            self.ahk_manager.send_key("space")
        
        return success_count
    
    # ===================================================
    # ЭКШЕНЫ (ОБНОВЛЕНО)
    # ===================================================
    
    def action_teleport_to_target(self, character):
        """
        Телепортировать персонажа к его таргету (БЕЗ space, БЕЗ проверок)
        """
        if not character:
            return False
        
        target_pos = character.char_base.get_target_position()
        
        if not target_pos:
            return False
        
        target_x, target_y, target_z = target_pos
        
        # Телепортируем с +2 к Z (БЕЗ space)
        return self.teleport_character(
            character, 
            target_x, 
            target_y, 
            target_z + 2,
            send_space=False
        )
    
    def tp_to_leader(self):
        """
        Телепортировать всех членов группы к лидеру (С space для всех)
        """
        leader, group = self.get_leader_and_group()
        
        if not leader:
            logging.warning("TP to LIDER: No valid leader found")
            return 0
        
        # Получаем координаты лидера
        leader.char_base.refresh()
        leader_x = leader.char_base.char_pos_x
        leader_y = leader.char_base.char_pos_y
        leader_z = leader.char_base.char_pos_z
        
        if leader_x is None or leader_y is None or leader_z is None:
            logging.error("TP to LIDER: Failed to read leader position")
            return 0
        
        # Фильтруем членов (без лидера, в радиусе 300м)
        members_to_tp = []
        
        for member in group:
            if member.char_base.char_id == leader.char_base.char_id:
                continue
            
            member.char_base.refresh()
            member_x = member.char_base.char_pos_x
            member_y = member.char_base.char_pos_y
            member_z = member.char_base.char_pos_z
            
            if member_x is None or member_y is None or member_z is None:
                continue
            
            distance = math.sqrt(
                (member_x - leader_x)**2 + 
                (member_y - leader_y)**2 + 
                (member_z - leader_z)**2
            )
            
            if distance <= 300:
                members_to_tp.append(member)
        
        # Телепортируем группу (С space)
        return self.teleport_group(members_to_tp, leader_x, leader_y, leader_z + 0.5)
    
    def tp_to_point(self, point_name):
        """
        УНИВЕРСАЛЬНАЯ функция телепорта к точке (SO, GO и т.д.)
        Телепортирует ТОЛЬКО последнее активное окно
        """
        active_char = self.app_state.last_active_character if self.app_state else None
        
        if not active_char:
            logging.warning(f"TP to {point_name}: No active character")
            return False
        
        # Найти точку по имени
        point = None
        for p in DUNGEON_POINTS:
            if p["name"] == point_name:
                point = p
                break
        
        if not point:
            logging.error(f"TP to {point_name}: Point not found")
            return False
        
        # Проверяем позицию персонажа
        active_char.char_base.refresh()
        char_x = active_char.char_base.char_pos_x
        char_y = active_char.char_base.char_pos_y
        
        if char_x is None or char_y is None:
            return False
        
        # Проверяем расстояние до триггера
        trigger_x, trigger_y = point["trigger"]
        radius = point["radius"]
        
        dx = abs(char_x - trigger_x)
        dy = abs(char_y - trigger_y)
        
        if dx <= radius and dy <= radius:
            # В зоне триггера - телепортируем (С space)
            target_x, target_y, target_z = point["target"]
            return self.teleport_character(active_char, target_x, target_y, target_z, send_space=True)
        else:
            char_name = active_char.char_base.char_name
            logging.info(f"TP to {point_name}: {char_name} not in trigger zone (dx={dx:.1f}, dy={dy:.1f})")
            return False
    
    # ===================================================
    # TELEPORT TOGGLE - ОПТИМИЗИРОВАННАЯ ЛОГИКА
    # ===================================================
    
    def check_teleport_conditions(self):
        """
        Проверить условия телепортации (ОПТИМИЗИРОВАНО)
        Вызывается каждую секунду из toggle loop
        
        Returns:
            str: статус проверки
        """
        if not self.world_manager or not self.app_state:
            return "❌ WorldManager or AppState not initialized"
        
        active_char = self.app_state.last_active_character
        leader, group = self.get_leader_and_group()
        
        # Проверяем является ли активное окно лидером
        is_leader = (active_char == leader)
        
        # === ПРОВЕРКА ВСЕХ ТОЧЕК ===
        for point in DUNGEON_POINTS:
            point_name = point["name"]
            mode = point["mode"]
            trigger_x, trigger_y = point["trigger"]
            radius = point["radius"]
            
            # === SOLO ТОЧКИ (любое активное окно) ===
            if mode == "solo":
                if not active_char:
                    continue
                
                active_char.char_base.refresh()
                char_x = active_char.char_base.char_pos_x
                char_y = active_char.char_base.char_pos_y
                
                if char_x is None or char_y is None:
                    continue
                
                # Проверка триггера
                dx = abs(char_x - trigger_x)
                dy = abs(char_y - trigger_y)
                
                if dx <= radius and dy <= radius:
                    # В триггере - проверяем лут если нужно
                    if point.get("check_loot", False):
                        if self.world_manager.has_any_loot():
                            loot_items = self.world_manager.get_loot_nearby(
                                (char_x, char_y, active_char.char_base.char_pos_z),
                                LOOT_CHECK_RADIUS
                            )
                            
                            if loot_items and len(loot_items) > 0:
                                return f"⏳ {point_name} (SOLO) - Waiting for loot ({len(loot_items)} items)"
                    
                    # Телепортируем
                    target_x, target_y, target_z = point["target"]
                    success = self.teleport_character(active_char, target_x, target_y, target_z, send_space=True)
                    
                    if success:
                        char_name = active_char.char_base.char_name
                        logging.info(f"✅ {point_name} (SOLO): {char_name} teleported")
                        return f"✅ {point_name} (SOLO) - Teleported"
            
            # === PARTY ТОЧКИ (только если активное окно = лидер) ===
            elif mode == "party":
                if not is_leader or not group:
                    continue
                
                leader.char_base.refresh()
                leader_x = leader.char_base.char_pos_x
                leader_y = leader.char_base.char_pos_y
                leader_z = leader.char_base.char_pos_z
                
                if leader_x is None or leader_y is None or leader_z is None:
                    continue
                
                # Проверка триггера лидера
                dx = abs(leader_x - trigger_x)
                dy = abs(leader_y - trigger_y)
                
                if dx <= radius and dy <= radius:
                    # Проверяем сколько персонажей в триггере
                    chars_in_trigger = []
                    
                    for char in group:
                        char.char_base.refresh()
                        char_x = char.char_base.char_pos_x
                        char_y = char.char_base.char_pos_y
                        
                        if char_x is None or char_y is None:
                            continue
                        
                        char_dx = abs(char_x - trigger_x)
                        char_dy = abs(char_y - trigger_y)
                        
                        if char_dx <= radius and char_dy <= radius:
                            chars_in_trigger.append(char)
                    
                    total_chars = len(group)
                    ready_chars = len(chars_in_trigger)
                    
                    # Не все в радиусе
                    if ready_chars < total_chars:
                        return f"⏳ {point_name} (PARTY) - {ready_chars}/{total_chars} ready"
                    
                    # Все в радиусе - проверяем лут если нужно
                    if point.get("check_loot", False):
                        if self.world_manager.has_any_loot():
                            loot_items = self.world_manager.get_loot_nearby(
                                (leader_x, leader_y, leader_z),
                                LOOT_CHECK_RADIUS
                            )
                            
                            if loot_items and len(loot_items) > 0:
                                return f"⏳ {point_name} (PARTY) - {ready_chars}/{total_chars} ready, {len(loot_items)} loot items"
                    
                    # ВСЕ УСЛОВИЯ ВЫПОЛНЕНЫ - телепортируем группу
                    target_x, target_y, target_z = point["target"]
                    success_count = self.teleport_group(chars_in_trigger, target_x, target_y, target_z)
                    
                    if success_count > 0:
                        logging.info(f"✅ {point_name} (PARTY): {success_count}/{total_chars} teleported")
                        return f"✅ {point_name} (PARTY) - Teleported {success_count}/{total_chars}"
        
        return "⏳ No trigger points active"
    
    # ===================================================
    # FOLLOW И ATTACK (БЕЗ ИЗМЕНЕНИЙ)
    # ===================================================

    def set_attack_target(self):
        """Установить таргет лидера всем членам группы"""
        leader, group = self.get_leader_and_group()
        
        if not leader:
            return 0
        
        leader.char_base.refresh()
        leader_target_id = leader.char_base.target_id
        
        if not leader_target_id or leader_target_id == 0:
            return 0
        
        success_count = 0
        
        for member in group:
            if member.char_base.char_id == leader.char_base.char_id:
                continue
            
            if member.char_base.set_target_id(leader_target_id):
                success_count += 1
        
        return success_count

    def follow_leader(self):
        """Синхронизация полета членов группы с лидером"""
        leader, group = self.get_leader_and_group()
        
        if not leader:
            return 0
        
        leader.char_base.refresh()
        leader_fly_status = leader.char_base.fly_status
        
        if leader_fly_status != 2:
            # Лидер не в полете - разморозить всех
            for member in group:
                if member.char_base.char_id == leader.char_base.char_id:
                    continue
                
                if member.fly_freeze_info and member.fly_freeze_info['active']:
                    member.memory.unfreeze_address(member.fly_freeze_info)
                    member.fly_freeze_info = None
                    member.char_base.set_fly_speed_z(0)
            
            return 0
        
        leader_z = leader.char_base.char_pos_z
        leader_fly_speed = leader.char_base.fly_speed
        
        if leader_z is None or leader_fly_speed is None:
            return 0
        
        active_corrections = 0
        
        for member in group:
            if member.char_base.char_id == leader.char_base.char_id:
                continue
            
            member.char_base.refresh()
            member_z = member.char_base.char_pos_z
            
            if member_z is None:
                continue
            
            z_diff = member_z - leader_z
            
            if z_diff < -1:
                # Подниматься
                target_fly_speed_z = leader_fly_speed
                
                if member.fly_freeze_info and member.fly_freeze_info['active']:
                    if member.fly_freeze_info['value'] != target_fly_speed_z:
                        member.memory.unfreeze_address(member.fly_freeze_info)
                        member.fly_freeze_info = None
                
                if not member.fly_freeze_info or not member.fly_freeze_info['active']:
                    member.char_base.set_fly_speed_z(target_fly_speed_z)
                    member.fly_freeze_info = member.memory.freeze_address(
                        member.char_base.cache["char_base"] + 0x12A8,
                        target_fly_speed_z,
                        'float',
                        0.1
                    )
                
                active_corrections += 1
            
            elif z_diff > 1:
                # Опускаться
                target_fly_speed_z = -leader_fly_speed
                
                if member.fly_freeze_info and member.fly_freeze_info['active']:
                    if member.fly_freeze_info['value'] != target_fly_speed_z:
                        member.memory.unfreeze_address(member.fly_freeze_info)
                        member.fly_freeze_info = None
                
                if not member.fly_freeze_info or not member.fly_freeze_info['active']:
                    member.char_base.set_fly_speed_z(target_fly_speed_z)
                    member.fly_freeze_info = member.memory.freeze_address(
                        member.char_base.cache["char_base"] + 0x12A8,
                        target_fly_speed_z,
                        'float',
                        0.1
                    )
                
                active_corrections += 1
            
            else:
                # Разморозить
                if member.fly_freeze_info and member.fly_freeze_info['active']:
                    member.memory.unfreeze_address(member.fly_freeze_info)
                    member.fly_freeze_info = None
                    member.char_base.set_fly_speed_z(0)
        
        return active_corrections