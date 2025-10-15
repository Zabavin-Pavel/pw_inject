"""
Управление несколькими игровыми процессами - ПОЛНОСТЬЮ ОБНОВЛЕНО
"""
import ctypes
import logging
import math
from game.memory import Memory
from game.structs import CharBase, WorldManager
from characters.character import Character
from config.constants import DUNGEON_POINTS, LOOT_CHECK_RADIUS
from game.win32_api import TH32CS_SNAPPROCESS, PROCESSENTRY32
from game.offsets import resolve_offset, OFFSETS


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
        self.action_limiter = None  # НОВОЕ: система лимитов
    
    def set_ahk_manager(self, ahk_manager):
        """Установить AHK менеджер"""
        self.ahk_manager = ahk_manager
    
    def set_app_state(self, app_state):
        """Установить app_state"""
        self.app_state = app_state
    
    def set_action_limiter(self, action_limiter):
        """Установить action_limiter"""
        self.action_limiter = action_limiter
    
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
            
            if pid == self._main_pid:
                self.world_manager = None
                self._main_pid = None
        
        # Проверяем смену персонажа для существующих процессов
        to_recreate = []
        for pid, char in list(self.characters.items()):
            char.char_base.refresh()
            
            if not char.char_base.is_valid():
                to_recreate.append(pid)
                continue
            
            if char.char_base._previous_char_id != char.char_base.char_id:
                logging.info(f"🔄 Character changed in PID {pid}, recreating...")
                to_recreate.append(pid)
            else:
                # НОВОЕ: Обновляем fly trigger кеш (только если персонаж не менялся)
                char.update_fly_trigger_cache()
        
        # Пересоздаём персонажей (смена персонажа или невалидность)
        for pid in to_recreate:
            old_char = self.characters[pid]
            char_base = CharBase(old_char.memory)
            new_char = Character(pid, old_char.memory, char_base)
            self.characters[pid] = new_char
            logging.info(f"✅ Character recreated for PID {pid}: {char_base.char_name}")
        
        # Добавляем новые процессы
        for pid in current_pids - existing_pids:
            mem = Memory()
            if mem.attach_by_pid(pid):
                char_base = CharBase(mem)
                logging.info(f"DEBUG PID={pid}: char_origin={hex(char_base.cache.get('char_origin', 0))}, char_base={hex(char_base.cache.get('char_base', 0))}")
                char = Character(pid, mem, char_base)
                self.characters[pid] = char
                
                if self._main_pid is None:
                    self._main_pid = pid
                    self.world_manager = WorldManager(mem)
                
                char_name = char_base.char_name if char_base.char_name else "???"
                logging.info(f"✅ New character added: PID={pid}, Name={repr(char_name)}")


        
        # НОВОЕ: Обновляем мапу pid↔char_id в AppState
        if self.app_state:
            self.app_state.update_pid_char_id_map(self.get_all_characters())
    
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
    # НОВАЯ УПРОЩЕННАЯ ЛОГИКА GET_LEADER_AND_GROUP
    # ===================================================
    
    def get_leader_and_group(self):
        """
        НОВАЯ ЛОГИКА: Взять последнего активного персонажа
        - Если он в пати → вернуть всех членов группы через оффсеты
        - Иначе → вернуть только его
        
        Returns:
            (leader: Character, members: list[Character])
            - leader: последний активный персонаж (или None)
            - members: [leader] если без пати, или вся группа если в пати
        """
        # Берем последнего активного персонажа
        leader = self.app_state.last_active_character if self.app_state else None
        
        if not leader or not leader.is_valid():
            return None, []
        
        # Обновляем данные лидера
        leader.char_base.refresh()
        
        # Проверяем есть ли пати
        party_ptr = resolve_offset(leader.memory, OFFSETS["party_ptr"], leader.char_base.cache)
        
        if not party_ptr or party_ptr == 0:
            # Нет пати - возвращаем только лидера
            return leader, [leader]
        
        # Есть пати - получаем всех членов группы
        leader.char_base.cache["party_ptr"] = party_ptr
        
        party_members = resolve_offset(leader.memory, OFFSETS["party_members"], leader.char_base.cache)
        
        if not party_members:
            return leader, [leader]
        
        # Собираем наших персонажей из группы
        group_chars = []
        
        for member in party_members:
            member_id = member.get('id')
            if not member_id:
                continue
            
            # Ищем персонажа по char_id через мапу
            if self.app_state:
                member_pid = self.app_state.get_pid_by_char_id(member_id)
                if member_pid and member_pid in self.characters:
                    char = self.characters[member_pid]
                    if char.is_valid():
                        group_chars.append(char)
        
        # Если не нашли никого - возвращаем только лидера
        if not group_chars:
            return leader, [leader]
        
        return leader, group_chars
    
    # ===================================================
    # ТИПОВЫЕ ФУНКЦИИ ТЕЛЕПОРТАЦИИ (С ПРОВЕРКОЙ ЛИЦЕНЗИИ)
    # ===================================================
    
    def teleport_character(self, character, target_x, target_y, target_z, send_space=False):
        """
        Телепортировать одного персонажа (БЫСТРО, БЕЗ ПРОВЕРОК)
        
        Args:
            character: персонаж для телепорта
            target_x, target_y, target_z: целевые координаты
            send_space: нужно ли нажать space после телепорта
        
        Returns:
            bool: всегда True (проверок нет)
        """
        if not character or not character.is_valid():
            return False
        
        # Записываем координаты (БЕЗ ПРОВЕРОК)
        character.char_base.set_position(target_x, target_y, target_z)
        
        # Нажимаем space если нужно (ОДИНОЧНЫЙ)
        if send_space and self.ahk_manager:
            self.ahk_manager.send_key_to_pid("space", character.pid)
        
        # НОВОЕ: Проверка лицензии в конце
        self._check_license_expiry()
        
        return True
    
    def teleport_group(self, characters, target_x, target_y, target_z, send_space=False):
        """
        Телепортировать группу персонажей (БЫСТРО, БЕЗ ПРОВЕРОК)
        
        Args:
            characters: список персонажей
            target_x, target_y, target_z: целевые координаты
            send_space: нужно ли нажать space после телепорта
        
        Returns:
            int: количество телепортированных персонажей
        """
        if not characters:
            return 0
        
        success_count = 0
        
        # Записываем координаты всем (БЕЗ ПРОВЕРОК)
        for char in characters:
            if char.is_valid():
                char.char_base.set_position(target_x, target_y, target_z)
                success_count += 1
        
        # Нажимаем space ВСЕМ СРАЗУ если нужно (МАССОВЫЙ)
        if send_space and success_count > 0 and self.ahk_manager:
            self.ahk_manager.send_key("space")
        
        # НОВОЕ: Проверка лицензии в конце
        self._check_license_expiry()
        
        return success_count
    
    def _check_license_expiry(self):
        """
        Проверка истечения лицензии
        Если срок истек - запускает принудительный refresh GUI
        """
        try:
            from core.license_manager import LicenseManager
            from datetime import datetime
            
            # Предполагаем что license_config доступен через GUI
            # Это быстрая проверка, не должна замедлять телепорт
            
            # TODO: Реализовать интеграцию с LicenseManager
            # Пока заглушка
            
        except Exception as e:
            logging.debug(f"License check skipped: {e}")
    
    # ===================================================
    # ЭКШЕНЫ (ОПТИМИЗИРОВАНО)
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
        
        # Телепортируем с +2 к Z (БЕЗ space, БЕЗ проверок)
        self.teleport_character(
            character, 
            target_x, 
            target_y, 
            target_z + 2,
            send_space=False
        )
        
        return True
    
    def tp_to_leader(self):
        """
        Телепортировать всех членов группы к лидеру (С МАССОВЫМ SPACE)
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
        
        # Телепортируем группу (С МАССОВЫМ SPACE)
        return self.teleport_group(
            members_to_tp, 
            leader_x, 
            leader_y, 
            leader_z + 0.5,
            send_space=True
        )
    
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
            # В зоне триггера - телепортируем (С ОДИНОЧНЫМ SPACE)
            target_x, target_y, target_z = point["target"]
            return self.teleport_character(
                active_char, 
                target_x, 
                target_y, 
                target_z,
                send_space=True
            )
        else:
            char_name = active_char.char_base.char_name
            logging.info(f"TP to {point_name}: {char_name} not in trigger zone (dx={dx:.1f}, dy={dy:.1f})")
            return False

    # ===================================================
    # FOLLOW (ИСПРАВЛЕНО)
    # Работает только для окон в пати, в одной локации, с лидером
    # ===================================================
    
    def follow_leader(self):
        """
        Синхронизация полета группы (ИСПРАВЛЕНО)
        
        Логика:
        1. Только для окон в пати
        2. Только если есть лидер среди наших окон
        3. Только для окон в той же локации что и лидер
        4. Лидера НЕ трогаем (не морозим, не меняем fly_trigger)
        5. Используем fly_trigger для управления полетом (если найдены оба состояния)
        
        Returns:
            int: количество активных корректировок
        """
        leader, group = self.get_leader_and_group()
        
        if not leader or len(group) <= 1:
            return 0
        
        # Обновляем данные лидера
        leader.char_base.refresh()
        
        leader_z = leader.char_base.char_pos_z
        leader_fly_status = leader.char_base.fly_status
        leader_location = leader.char_base.location_id
        
        if leader_z is None or leader_fly_status is None or leader_location is None:
            return 0
        
        active_corrections = 0
        
        for member in group:
            # Пропускаем лидера
            if member.char_base.char_id == leader.char_base.char_id:
                continue
            
            member.char_base.refresh()
            
            # Проверка локации (КРИТИЧНО!)
            member_location = member.char_base.location_id
            if member_location != leader_location:
                # Окно в другой локации - пропускаем
                continue
            
            member_z = member.char_base.char_pos_z
            member_fly_status = member.char_base.fly_status
            
            if member_z is None or member_fly_status is None:
                continue
            
            # Разница по высоте
            z_diff = abs(member_z - leader_z)
            
            # УПРАВЛЕНИЕ ПОЛЕТОМ (если найдены оба состояния)
            if member.can_control_flight():
                # Лидер летит, а член не летит
                if leader_fly_status == 1 and member_fly_status != 1:
                    member.set_flight_state(True)
                    logging.debug(f"✈️ {member.char_base.char_name} взлетает")
                
                # Лидер не летит, а член летит
                elif leader_fly_status != 1 and member_fly_status == 1:
                    member.set_flight_state(False)
                    logging.debug(f"🚶 {member.char_base.char_name} приземляется")
            
            # РЕГУЛИРОВАНИЕ ВЫСОТЫ
            if leader_fly_status == 1:  # Лидер летит
                if z_diff > 1.0:  # Разница больше 1м
                    # Заморозить высоту на уровне лидера
                    if not member.fly_freeze_info or not member.fly_freeze_info.get('active'):
                        # Морозим
                        freeze_info = member.memory.freeze_address(
                            member.char_base.cache["char_base"] + 0x9FC,  # char_pos_z
                            leader_z
                        )
                        
                        if freeze_info:
                            member.fly_freeze_info = freeze_info
                            member.char_base.set_fly_speed_z(0)
                            active_corrections += 1
                            logging.debug(f"❄️ {member.char_base.char_name} заморожен на высоте {leader_z:.1f}")
                else:
                    # Высота в пределах нормы - разморозить если был заморожен
                    if member.fly_freeze_info and member.fly_freeze_info.get('active'):
                        member.memory.unfreeze_address(member.fly_freeze_info)
                        member.fly_freeze_info = None
                        member.char_base.set_fly_speed_z(0)
                        logging.debug(f"🔓 {member.char_base.char_name} разморожен")
            else:
                # Лидер не летит - разморозить всех
                if member.fly_freeze_info and member.fly_freeze_info.get('active'):
                    member.memory.unfreeze_address(member.fly_freeze_info)
                    member.fly_freeze_info = None
                    member.char_base.set_fly_speed_z(0)
        
        return active_corrections
    
    # ===================================================
    # ATTACK (ИСПРАВЛЕНО)
    # ===================================================
    
    def set_attack_target(self):
        """
        Установить таргет лидера всем членам группы (ИСПРАВЛЕНО)
        
        Returns:
            int: количество успешных установок
        """
        leader, group = self.get_leader_and_group()
        
        if not leader or len(group) <= 1:
            return 0
        
        leader.char_base.refresh()
        leader_target_id = leader.char_base.target_id
        
        if not leader_target_id or leader_target_id == 0:
            return 0
        
        success_count = 0
        
        for member in group:
            # Пропускаем лидера
            if member.char_base.char_id == leader.char_base.char_id:
                continue
            
            # Устанавливаем target_id
            if member.char_base.set_target_id(leader_target_id):
                success_count += 1
        
        return success_count