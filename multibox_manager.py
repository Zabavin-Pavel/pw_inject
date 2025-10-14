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
    
    def action_teleport_to_target(self, character):
        """
        Телепортировать персонажа к его таргету
        Args:
            character: персонаж для телепорта
        Returns:
            bool: успех операции
        """
        if not character:
            return False
        
        # Получаем координаты таргета
        target_pos = character.char_base.get_target_position()
        
        if not target_pos:
            return False
        
        target_x, target_y, target_z = target_pos
        
        # Телепортируем с +1 к Z
        new_z = target_z + 2
        
        success = character.char_base.set_position(target_x, target_y, new_z)
        
        if success:
            print(f"✅ {character.char_base.char_name}: Телепорт → ({target_x:.2f}, {target_y:.2f}, {new_z:.2f})")
        
        return success

    # ===================================================
    # НОВЫЕ МЕТОДЫ - ДОБАВИТЬ В КОНЕЦ MultiboxManager
    # ===================================================

    def get_leader_and_group(self):
        """
        НОВОЕ: Найти группу с максимальным числом наших персонажей и вернуть лидера + членов
        
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

    def tp_to_leader(self):
        """
        НОВОЕ: Телепортировать всех членов группы к лидеру
        
        Логика:
        - Найти группу с максимальным числом наших персонажей
        - Проверить что лидер - один из наших персонажей
        - Телепортировать всех членов (кроме лидера) к координатам лидера + 0.5 по Z
        - Пропускать персонажей дальше 300 метров от лидера
        
        Returns:
            int: количество успешных телепортов
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
        
        tp_count = 0
        
        for member in group:
            # Пропускаем лидера
            if member.char_base.char_id == leader.char_base.char_id:
                continue
            
            # Обновляем позицию члена группы
            member.char_base.refresh()
            member_x = member.char_base.char_pos_x
            member_y = member.char_base.char_pos_y
            member_z = member.char_base.char_pos_z
            
            if member_x is None or member_y is None or member_z is None:
                continue
            
            # Проверка расстояния (пропускаем если дальше 300м)
            distance = math.sqrt((member_x - leader_x)**2 + (member_y - leader_y)**2 + (member_z - leader_z)**2)
            
            if distance > 300:
                logging.info(f"TP to LIDER: {member.char_base.char_name} too far ({distance:.1f}m) - skipped")
                continue
            
            # Телепортируем к лидеру (Z + 0.5)
            success = member.char_base.set_position(leader_x, leader_y, leader_z + 0.5)
            
            if success:
                tp_count += 1
                logging.info(f"✅ TP to LIDER: {member.char_base.char_name} → Leader")
        
        return tp_count

    def set_attack_target(self):
        """
        НОВОЕ: Установить таргет лидера всем членам группы (для Attack toggle)
        
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
        НОВОЕ: Синхронизация полета членов группы с лидером (для Follow toggle)
        
        Логика:
        - Проверить что лидер в полете (fly_status == 2)
        - Для каждого члена:
        - Если ниже лидера > 5м: установить fly_speed_z = fly_speed (подниматься)
        - Если выше лидера > 5м: установить fly_speed_z = -fly_speed (опускаться)
        - Если разница <= 5м: установить fly_speed_z = 0 и разморозить
        
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
            if z_diff < -5:
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
            
            elif z_diff > 5:
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
                # Разница <= 5м - установить 0 и разморозить
                if member.fly_freeze_info and member.fly_freeze_info['active']:
                    member.memory.unfreeze_address(member.fly_freeze_info)
                    member.fly_freeze_info = None
                    member.char_base.set_fly_speed_z(0)
                    logging.debug(f"Follow: {member.char_base.char_name} = (z_diff: {z_diff:.1f}m) - leveled")
        
        return active_corrections