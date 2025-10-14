"""
Управление несколькими игровыми процессами
"""
import ctypes
from win32_api import TH32CS_SNAPPROCESS, PROCESSENTRY32
from memory import Memory
from game_structs import CharBase, WorldManager
from character import Character

class MultiboxManager:
    """Управление группой персонажей"""
    
    def __init__(self):
        self.characters = {}  # {pid: Character}
        self.kernel32 = ctypes.windll.kernel32
        self._leader_char_id = None
        
        # WorldManager для первого процесса (главный)
        self.world_manager = None
        self._main_pid = None
        
        # НОВОЕ: Для телепортации
        self.ahk_manager = None  # Будет установлен из GUI
        self.app_state = None    # Будет установлен из GUI
        
        # НОВОЕ: Состояние для Teleport toggle
        self.teleport_state = {
            "active_point": None,
            "teleporting_pids": set(),
        }
    
    def set_ahk_manager(self, ahk_manager):
        """Установить AHK менеджер для отправки клавиш"""
        self.ahk_manager = ahk_manager
    
    def set_app_state(self, app_state):
        """Установить app_state для доступа к last_active_character"""
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
        """Алиас для refresh() - для совместимости с GUI"""
        self.refresh()
    
    def get_nearby_loot(self, character=None):
        """
        Получить лут вокруг
        Args:
            character: персонаж для сканирования (если None - главный процесс)
        """
        if not self.world_manager:
            return []
        
        # Если персонаж не указан - используем первого валидного
        if character is None:
            chars = self.get_all_characters()
            if not chars:
                return []
            character = chars[0]
        
        # Получаем позицию персонажа
        x, y, z = character.char_base.position
        
        # Получаем лут вокруг
        return self.world_manager.get_nearby_loot(x, y)

    def get_nearby_players(self, character=None):
        """Получить игроков вокруг"""
        # TODO: Реализовать когда будет готов WorldManager
        return []

    def get_nearby_npcs(self, character=None):
        """Получить NPC вокруг"""
        # TODO: Реализовать когда будет готов WorldManager
        return []
    
    def update_leader(self):
        """Обновить лидера из памяти"""
        new_leader = None
        
        for char in self.characters.values():
            if char.char_base.is_valid() and char.char_base.is_leader:
                new_leader = char.char_base.char_id
                break
        
        if new_leader != self._leader_char_id:
            self._leader_char_id = new_leader
    
    def get_leader(self):
        """Получить персонажа-лидера"""
        if not self._leader_char_id:
            return None
        
        for char in self.characters.values():
            if char.char_base.is_valid() and char.char_base.char_id == self._leader_char_id:
                return char
        return None
    
    def get_followers(self):
        """Получить всех последователей (не лидеров)"""
        followers = []
        for char in self.characters.values():
            if char.char_base.is_valid() and char.char_base.char_id != self._leader_char_id:
                followers.append(char)
        return followers
    
    def get_all_characters(self):
        """Получить список всех ВАЛИДНЫХ персонажей"""
        valid_chars = []
        for char in self.characters.values():
            if char.is_valid():
                valid_chars.append(char)
        return valid_chars
    
    def get_valid_characters(self):
        """Алиас для get_all_characters() - для совместимости с GUI"""
        return self.get_all_characters()
    
    def get_total_count(self):
        """Получить общее количество процессов (включая невалидные)"""
        return len(self.characters)
    
    def get_valid_count(self):
        """Получить количество валидных персонажей"""
        return len([c for c in self.characters.values() if c.is_valid()])
    
    # ===================================================
    # LEADER AND GROUP
    # ===================================================

    def get_leader_and_group(self):
        """
        Найти группу с максимальным числом наших персонажей и вернуть лидера + членов
        
        Returns:
            (leader: Character, members: list[Character]) или (None, [])
        """
        import logging
        from offsets import resolve_offset, OFFSETS
        
        # Собираем информацию о группах
        groups = {}  # {leader_id: [char1, char2, ...]}
        
        for char in self.get_all_characters():
            char.char_base.refresh()
            
            # Получаем party_ptr
            party_ptr = resolve_offset(char.memory, OFFSETS["party_ptr"], char.char_base.cache)
            
            if not party_ptr or party_ptr == 0:
                continue  # Персонаж не в группе
            
            char.char_base.cache["party_ptr"] = party_ptr
            
            # Получаем leader_id
            party_leader_id = resolve_offset(char.memory, OFFSETS["party_leader_id"], char.char_base.cache)
            
            if not party_leader_id:
                continue
            
            # Добавляем персонажа в группу
            if party_leader_id not in groups:
                groups[party_leader_id] = []
            
            groups[party_leader_id].append(char)
        
        if not groups:
            logging.warning("No groups found")
            return None, []
        
        # Находим самую большую группу
        largest_group_leader_id = max(groups.keys(), key=lambda lid: len(groups[lid]))
        largest_group = groups[largest_group_leader_id]
        
        # Находим лидера среди наших персонажей
        leader = None
        for char in largest_group:
            if char.char_base.char_id == largest_group_leader_id:
                leader = char
                break
        
        if not leader:
            logging.warning(f"Leader (ID {largest_group_leader_id}) not found among our characters")
            return None, []
        
        logging.info(f"Leader: {leader.char_base.char_name}, Group size: {len(largest_group)}")
        
        return leader, largest_group

    # ===================================================
    # ТИПОВЫЕ ФУНКЦИИ ТЕЛЕПОРТАЦИИ
    # ===================================================
    
    def teleport_character(self, character, target_x, target_y, target_z, verify_timeout=2.0, send_space=True):
        """
        Телепортировать одного персонажа с проверкой
        
        Args:
            character: персонаж для телепорта
            target_x, target_y, target_z: целевые координаты
            verify_timeout: таймаут проверки (секунды)
            send_w: нужно ли нажать W после записи координат
        
        Returns:
            bool: успех операции
        """
        import time
        import math
        import logging
        
        if not character or not character.is_valid():
            return False
        
        char_name = character.char_base.char_name
        
        # Записываем координаты
        success = character.char_base.set_position(target_x, target_y, target_z)
        
        if not success:
            logging.error(f"TP: {char_name} - Failed to write coordinates")
            return False
        
        # Нажимаем space для триггера обновления
        if send_space and self.ahk_manager:
            self.ahk_manager.send_key_to_pid("space", character.pid)
            time.sleep(0.05)
        
        # Ждем и проверяем позицию
        time.sleep(verify_timeout)
        
        character.char_base.refresh()
        actual_x = character.char_base.char_pos_x
        actual_y = character.char_base.char_pos_y
        actual_z = character.char_base.char_pos_z
        
        if actual_x is None or actual_y is None or actual_z is None:
            logging.error(f"TP: {char_name} - Failed to read position after teleport")
            return False
        
        # Проверяем расстояние до цели (допустимая погрешность 5м)
        distance = math.sqrt(
            (actual_x - target_x)**2 + 
            (actual_y - target_y)**2 + 
            (actual_z - target_z)**2
        )
        
        if distance <= 5:
            logging.info(f"✅ TP: {char_name} → ({target_x:.0f}, {target_y:.0f}, {target_z:.0f})")
            return True
        else:
            logging.warning(f"⚠️ TP: {char_name} - Knocked back (distance: {distance:.1f}m)")
            return False
    
    def teleport_group(self, characters, target_x, target_y, target_z, max_retries=3):
        """
        Телепортировать группу персонажей
        
        Args:
            characters: список персонажей
            target_x, target_y, target_z: целевые координаты
            max_retries: максимум попыток для каждого персонажа
        
        Returns:
            int: количество успешных телепортов
        """
        import time
        import logging
        
        if not characters:
            return 0
        
        success_count = 0
        failed_chars = []
        
        # Фаза 1: Групповая телепортация (записываем координаты + W всем)
        logging.info(f"TP Group: Phase 1 - Group teleport ({len(characters)} characters)")
        
        for char in characters:
            if char.is_valid():
                char.char_base.set_position(target_x, target_y, target_z)
        
        # Отправляем W всем
        if self.ahk_manager:
            self.ahk_manager.send_key("W")
        
        # Ждем завершения телепортации
        time.sleep(2.0)
        
        # Проверяем кто телепортировался успешно
        for char in characters:
            if not char.is_valid():
                continue
            
            char.char_base.refresh()
            actual_x = char.char_base.char_pos_x
            actual_y = char.char_base.char_pos_y
            actual_z = char.char_base.char_pos_z
            
            if actual_x is None or actual_y is None or actual_z is None:
                failed_chars.append(char)
                continue
            
            import math
            distance = math.sqrt(
                (actual_x - target_x)**2 + 
                (actual_y - target_y)**2 + 
                (actual_z - target_z)**2
            )
            
            if distance <= 5:
                success_count += 1
                logging.info(f"✅ TP Group: {char.char_base.char_name} - Success")
            else:
                failed_chars.append(char)
                logging.warning(f"⚠️ TP Group: {char.char_base.char_name} - Failed (distance: {distance:.1f}m)")
        
        # Фаза 2: Индивидуальная телепортация для отставших
        if failed_chars and success_count >= len(characters) * 0.5:
            logging.info(f"TP Group: Phase 2 - Individual teleport ({len(failed_chars)} characters)")
            
            for char in failed_chars:
                for attempt in range(max_retries):
                    if self.teleport_character(char, target_x, target_y, target_z, verify_timeout=2.0):
                        success_count += 1
                        break
                    
                    if attempt < max_retries - 1:
                        logging.info(f"TP Group: {char.char_base.char_name} - Retry {attempt + 1}/{max_retries}")
                        time.sleep(1.0)
        
        return success_count
    
    # ===================================================
    # TELEPORT TOGGLE - ЛОГИКА
    # ===================================================
    
    def check_teleport_conditions(self):
        """
        Проверить условия телепортации и выполнить если готово
        Вызывается каждые 5 секунд из toggle loop
        
        Returns:
            str: статус проверки для вывода в консоль
        """
        import logging
        import math
        from constants import DUNGEON_POINTS
        
        leader, group = self.get_leader_and_group()
        
        if not leader:
            return "❌ No leader found"
        
        if not group or len(group) < 2:
            return "❌ Group too small (need at least 2 members)"
        
        # Обновляем позицию лидера
        leader.char_base.refresh()
        leader_x = leader.char_base.char_pos_x
        leader_y = leader.char_base.char_pos_y
        
        if leader_x is None or leader_y is None:
            return "❌ Failed to read leader position"
        
        # Ищем активную точку (лидер в радиусе триггера)
        active_point = None
        
        for point in DUNGEON_POINTS:
            trigger_x, trigger_y = point["trigger"]
            radius = point["radius"]
            
            dx = abs(leader_x - trigger_x)
            dy = abs(leader_y - trigger_y)
            
            if dx <= radius and dy <= radius:
                active_point = point
                break
        
        if not active_point:
            return f"⏳ No trigger point (Leader at {leader_x:.0f}, {leader_y:.0f})"
        
        point_name = active_point["name"]
        mode = active_point["mode"]
        
        # === РЕЖИМ SOLO ===
        if mode == "solo":
            # Телепортируем только последнее активное окно
            if not self.app_state or not self.app_state.last_active_character:
                return f"⏳ Point '{point_name}' (SOLO) - No active character"
            
            active_char = self.app_state.last_active_character
            
            # Проверка лута если нужно
            if active_point.get("check_loot", False):
                # Получаем лут вокруг активного персонажа
                active_char.char_base.refresh()
                char_x = active_char.char_base.char_pos_x
                char_y = active_char.char_base.char_pos_y
                char_z = active_char.char_base.char_pos_z
                
                if char_x is not None and char_y is not None and char_z is not None:
                    loot_items = self.world_manager.get_loot_nearby(
                        (char_x, char_y, char_z),
                        max_distance=50
                    )
                    
                    if loot_items and len(loot_items) > 0:
                        return f"⏳ Point '{point_name}' (SOLO) - Waiting for loot ({len(loot_items)} items)"
            
            # Телепортируем
            target_x, target_y, target_z = active_point["target"]
            success = self.teleport_character(active_char, target_x, target_y, target_z)
            
            if success:
                return f"✅ Point '{point_name}' (SOLO) - Teleported"
            else:
                return f"❌ Point '{point_name}' (SOLO) - Teleport failed"
        
        # === РЕЖИМ PARTY ===
        # Проверяем сколько персонажей в радиусе триггера
        chars_in_radius = []
        
        for char in group:
            char.char_base.refresh()
            char_x = char.char_base.char_pos_x
            char_y = char.char_base.char_pos_y
            
            if char_x is None or char_y is None:
                continue
            
            trigger_x, trigger_y = active_point["trigger"]
            radius = active_point["radius"]
            
            dx = abs(char_x - trigger_x)
            dy = abs(char_y - trigger_y)
            
            if dx <= radius and dy <= radius:
                chars_in_radius.append(char)
        
        total_chars = len(group)
        ready_chars = len(chars_in_radius)
        
        # Не все в радиусе
        if ready_chars < total_chars:
            return f"⏳ Point '{point_name}' - {ready_chars}/{total_chars} characters ready"
        
        # Все в радиусе - проверяем лут если нужно
        if active_point.get("check_loot", False):
            # Получаем лут вокруг лидера
            loot_items = self.world_manager.get_loot_nearby(
                (leader_x, leader_y, leader.char_base.char_pos_z),
                max_distance=50
            )
            
            if loot_items and len(loot_items) > 0:
                return f"⏳ Point '{point_name}' - {ready_chars}/{total_chars} ready, but {len(loot_items)} loot items"
        
        # ВСЕ УСЛОВИЯ ВЫПОЛНЕНЫ - ТЕЛЕПОРТИРУЕМ
        target_x, target_y, target_z = active_point["target"]
        success_count = self.teleport_group(chars_in_radius, target_x, target_y, target_z)
        
        if success_count > 0:
            return f"✅ Point '{point_name}' - Teleported {success_count}/{total_chars} characters"
        else:
            return f"❌ Point '{point_name}' - Teleport failed"
    
    # ===================================================
    # ЭКШЕНЫ (ОБНОВЛЕННЫЕ)
    # ===================================================
    
    def action_teleport_to_target(self, character):
        """
        Телепортировать персонажа к его таргету (ОБНОВЛЕНО)
        """
        if not character:
            return False
        
        # Получаем координаты таргета
        target_pos = character.char_base.get_target_position()
        
        if not target_pos:
            return False
        
        target_x, target_y, target_z = target_pos
        
        # Телепортируем с +2 к Z (используем типовую функцию)
        return self.teleport_character(
            character, 
            target_x, 
            target_y, 
            target_z + 2,
            verify_timeout=2.0,
            send_space=False,
        )
    
    def tp_to_leader(self):
        """
        Телепортировать всех членов группы к лидеру (ОБНОВЛЕНО)
        """
        import logging
        import math
        
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
        
        # Отфильтровываем членов (без лидера, в радиусе 300м)
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
            else:
                logging.info(f"TP to LIDER: {member.char_base.char_name} too far ({distance:.1f}m) - skipped")
        
        # Телепортируем группу (используем типовую функцию)
        return self.teleport_group(members_to_tp, leader_x, leader_y, leader_z + 0.5)

    # ===================================================
    # FOLLOW И ATTACK (БЕЗ ИЗМЕНЕНИЙ)
    # ===================================================

    def set_attack_target(self):
        """
        Установить таргет лидера всем членам группы (для Attack toggle)
        
        Returns:
            int: количество успешных операций
        """
        import logging
        
        leader, group = self.get_leader_and_group()
        
        if not leader:
            logging.warning("Attack: No valid leader found")
            return 0
        
        # Получаем target_id лидера
        leader.char_base.refresh()
        leader_target_id = leader.char_base.target_id
        
        if not leader_target_id or leader_target_id == 0:
            logging.debug("Attack: Leader has no target")
            return 0
        
        success_count = 0
        
        for member in group:
            # Пропускаем лидера
            if member.char_base.char_id == leader.char_base.char_id:
                continue
            
            # Записываем target_id
            if member.char_base.set_target_id(leader_target_id):
                success_count += 1
                logging.debug(f"Attack: {member.char_base.char_name} → Target ID {leader_target_id}")
        
        return success_count

    def follow_leader(self):
        """
        Синхронизация полета членов группы с лидером (для Follow toggle)
        
        Returns:
            int: количество активных корректировок
        """
        import logging
        
        leader, group = self.get_leader_and_group()
        
        if not leader:
            return 0
        
        # Обновляем данные лидера
        leader.char_base.refresh()
        leader_fly_status = leader.char_base.fly_status
        
        # Проверяем что лидер в полете
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
        
        # Лидер в полете
        leader_z = leader.char_base.char_pos_z
        leader_fly_speed = leader.char_base.fly_speed
        
        if leader_z is None or leader_fly_speed is None:
            return 0
        
        active_corrections = 0
        
        for member in group:
            # Пропускаем лидера
            if member.char_base.char_id == leader.char_base.char_id:
                continue
            
            # Обновляем данные члена
            member.char_base.refresh()
            member_z = member.char_base.char_pos_z
            
            if member_z is None:
                continue
            
            z_diff = member_z - leader_z
            
            # Проверяем разницу по высоте
            if z_diff < -1:
                # Член ниже лидера - подниматься
                target_fly_speed_z = leader_fly_speed
                
                # Разморозить если заморожен на другое значение
                if member.fly_freeze_info and member.fly_freeze_info['active']:
                    if member.fly_freeze_info['value'] != target_fly_speed_z:
                        member.memory.unfreeze_address(member.fly_freeze_info)
                        member.fly_freeze_info = None
                
                # Заморозить на новое значение
                if not member.fly_freeze_info or not member.fly_freeze_info['active']:
                    member.char_base.set_fly_speed_z(target_fly_speed_z)
                    member.fly_freeze_info = member.memory.freeze_address(
                        member.char_base.cache["char_base"] + 0x12A8,
                        target_fly_speed_z,
                        'float',
                        0.1
                    )
                
                active_corrections += 1
                logging.debug(f"Follow: {member.char_base.char_name} ↑ (z_diff: {z_diff:.1f}m)")
            
            elif z_diff > 1:
                # Член выше лидера - опускаться
                target_fly_speed_z = -leader_fly_speed
                
                # Разморозить если заморожен на другое значение
                if member.fly_freeze_info and member.fly_freeze_info['active']:
                    if member.fly_freeze_info['value'] != target_fly_speed_z:
                        member.memory.unfreeze_address(member.fly_freeze_info)
                        member.fly_freeze_info = None
                
                # Заморозить на новое значение
                if not member.fly_freeze_info or not member.fly_freeze_info['active']:
                    member.char_base.set_fly_speed_z(target_fly_speed_z)
                    member.fly_freeze_info = member.memory.freeze_address(
                        member.char_base.cache["char_base"] + 0x12A8,
                        target_fly_speed_z,
                        'float',
                        0.1
                    )
                
                active_corrections += 1
                logging.debug(f"Follow: {member.char_base.char_name} ↓ (z_diff: {z_diff:.1f}m)")
            
            else:
                # Разница <= 1м - установить 0 и разморозить
                if member.fly_freeze_info and member.fly_freeze_info['active']:
                    member.memory.unfreeze_address(member.fly_freeze_info)
                    member.fly_freeze_info = None
                    member.char_base.set_fly_speed_z(0)
                    logging.debug(f"Follow: {member.char_base.char_name} = (z_diff: {z_diff:.1f}m) - leveled")
        
        return active_corrections