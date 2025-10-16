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
        self.characters = {}
        self.kernel32 = ctypes.windll.kernel32
        
        # WorldManager для первого процесса
        self.world_manager = None
        self._main_pid = None
        
        # Зависимости
        self.ahk_manager = None
        self.app_state = None
        self.action_limiter = None
        
        # НОВОЕ: Кеш группы (обновляется Attack каждые 500ms)
        self.party_cache = {
            'timestamp': None,  # время последнего обновления
            'leader': None,  # Character объект лидера
            'members': [],  # список Character объектов в группе
            'member_info': {}  # {char_id: {'pid': ..., 'location_id': ..., 'name': ...}}
        }
    
        # НОВОЕ: Единый поток заморозки для Follow
        self.freeze_thread = None
        self.freeze_stop_event = None
        self.freeze_targets = {}  # {pid: {'address': ..., 'value': ...}}

    def start_follow_freeze(self):
        """Запустить единый поток заморозки для Follow"""
        if self.freeze_thread and self.freeze_thread.is_alive():
            return
        
        import threading
        import time
        
        self.freeze_stop_event = threading.Event()
        self.freeze_targets = {}
        
        def freeze_loop():
            while not self.freeze_stop_event.is_set():
                for pid, target in list(self.freeze_targets.items()):
                    if pid in self.characters:
                        char = self.characters[pid]
                        char.memory.write_float(target['address'], target['value'])
                
                time.sleep(0.05)
        
        self.freeze_thread = threading.Thread(target=freeze_loop, daemon=True)
        self.freeze_thread.start()

    def stop_follow_freeze(self):
        """Остановить поток заморозки"""
        if self.freeze_stop_event:
            self.freeze_stop_event.set()
        self.freeze_targets = {}
        self.freeze_thread = None

    def _update_party_cache(self):
        """
        Обновить кеш группы
        
        Читает party_ptr, leader_id, собирает всех членов группы.
        Вызывается Attack каждый тик (500ms).
        """
        import time
        from game.offsets import resolve_offset, OFFSETS
        
        # Сбрасываем кеш
        self.party_cache['leader'] = None
        self.party_cache['members'] = []
        self.party_cache['member_info'] = {}
        
        all_chars = self.get_all_characters()
        
        if not all_chars:
            return
        
        # Берем первое окно для чтения party_leader_id
        first_char = all_chars[0]
        first_char.char_base.refresh()
        
        # Читаем party_ptr
        party_ptr = resolve_offset(
            first_char.memory,
            OFFSETS["party_ptr"],
            first_char.char_base.cache
        )
        
        if not party_ptr or party_ptr == 0:
            # Нет пати
            self.party_cache['timestamp'] = time.time()
            return
        
        # ЗАПИСЫВАЕМ В КЕШ
        first_char.char_base.cache["party_ptr"] = party_ptr
        
        # Читаем party_leader_id
        party_leader_id = resolve_offset(
            first_char.memory,
            OFFSETS["party_leader_id"],
            first_char.char_base.cache
        )
        
        if not party_leader_id or party_leader_id == 0:
            self.party_cache['timestamp'] = time.time()
            return
        
        # Ищем лидера (быстро через map)
        leader = None
        
        if self.app_state:
            leader_pid = self.app_state.get_pid_by_char_id(party_leader_id)
            if leader_pid and leader_pid in self.characters:
                leader = self.characters[leader_pid]
        
        # Fallback: ищем напрямую
        if not leader:
            for char in all_chars:
                char.char_base.refresh()
                if char.char_base.char_id == party_leader_id:
                    leader = char
                    break
        
        if not leader:
            self.party_cache['timestamp'] = time.time()
            return
        
        # Собираем всех членов группы (все окна с party_ptr != 0)
        members = []
        
        for char in all_chars:
            char.char_base.refresh()
            
            # Проверяем party_ptr
            char_party_ptr = resolve_offset(
                char.memory,
                OFFSETS["party_ptr"],
                char.char_base.cache
            )
            
            if not char_party_ptr or char_party_ptr == 0:
                continue
            
            char.char_base.cache["party_ptr"] = char_party_ptr
            
            members.append(char)
            
            # Заполняем member_info
            self.party_cache['member_info'][char.char_base.char_id] = {
                'pid': char.pid,
                'location_id': char.char_base.location_id,
                'name': char.char_base.char_name
            }
        
        # Сохраняем в кеш
        self.party_cache['leader'] = leader
        self.party_cache['members'] = members
        self.party_cache['timestamp'] = time.time()
        
        print(f"🔄 Party cache updated: leader={leader.char_base.char_name}, members={len(members)}")

    def _get_party_cache(self, force_update=False):
        """
        Получить кеш группы с проверкой актуальности
        
        Args:
            force_update: принудительно обновить кеш
        
        Returns:
            dict: party_cache
        """
        import time
        
        # Проверяем актуальность (1 секунда)
        if force_update or not self.party_cache['timestamp'] or (time.time() - self.party_cache['timestamp']) > 1.0:
            self._update_party_cache()
        
        return self.party_cache

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
        
        # ИСПРАВЛЕНО: Обновляем мапу pid↔char_id ВСЕГДА в конце refresh
        if self.app_state:
            self.app_state.update_pid_char_id_map(self.get_all_characters())
            logging.debug(f"🔄 Map updated: {self.app_state.char_id_to_pid}")
    
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
        Найти лидера и группу среди наших окон (ДИАГНОСТИКА)
        
        Returns:
            (leader, group): лидер и список участников группы, или (None, [])
        """
        # ИМПОРТ В НАЧАЛЕ!
        from game.offsets import resolve_offset, OFFSETS
        
        print("\n🔍 get_leader_and_group() вызван")
        print(f"   Всего окон: {len(self.characters)}")
        
        # Собираем всех персонажей с валидными данными
        valid_chars = []
        
        for pid, char in self.characters.items():
            print(f"\n   --- PID {pid} ---")
            
            if not char.char_base.is_valid():
                print(f"   ❌ Не валиден")
                continue
            
            char.char_base.refresh()
            
            char_name = char.char_base.char_name
            char_id = char.char_base.char_id
            
            # Читаем party_ptr
            party_ptr = resolve_offset(
                char.memory, 
                OFFSETS["party_ptr"], 
                char.char_base.cache
            )

            if not party_ptr or party_ptr == 0:
                print(f"   ❌ Нет party_ptr")
                continue

            # ЗАПИСАТЬ В КЕШ!
            char.char_base.cache["party_ptr"] = party_ptr
            
            print(f"   Имя: {char_name}")
            print(f"   ID: {char_id}")
            print(f"   party_ptr: {hex(party_ptr) if party_ptr else 'NULL'}")
            
            # Читаем данные группы
            party_leader_id = resolve_offset(char.memory, OFFSETS["party_leader_id"], char.char_base.cache)
            party_count = resolve_offset(char.memory, OFFSETS["party_count"], char.char_base.cache)
            
            print(f"   party_leader_id: {party_leader_id}")
            print(f"   party_count: {party_count}")
            
            if not party_leader_id or party_leader_id == 0:
                print(f"   ❌ Нет лидера группы")
                continue
            
            if not party_count or party_count <= 0:
                print(f"   ❌ Группа пустая")
                continue
            
            print(f"   ✅ В группе")
            valid_chars.append(char)
        
        print(f"\n📊 Валидных персонажей в группе: {len(valid_chars)}")
        
        if not valid_chars:
            print("❌ Нет персонажей в группе")
            return None, []
        
        # Ищем лидера среди наших окон
        leader = None
        
        for char in valid_chars:
            char.char_base.refresh()
            party_leader_id = resolve_offset(char.memory, OFFSETS["party_leader_id"], char.char_base.cache)
            
            print(f"\n🔍 Проверяем {char.char_base.char_name}:")
            print(f"   char_id: {char.char_base.char_id}")
            print(f"   party_leader_id: {party_leader_id}")
            
            if char.char_base.char_id == party_leader_id:
                leader = char
                print(f"   ✅ ЭТО ЛИДЕР!")
                break
        
        if not leader:
            print("❌ Лидер не найден среди наших окон")
            return None, []
        
        print(f"\n✅ Лидер найден: {leader.char_base.char_name}")
        print(f"✅ Группа: {len(valid_chars)} участников")
        
        return leader, valid_chars
        
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
            self.ahk_manager.send_key("Space")
        
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
        """Follow с единым потоком заморозки"""
        cache = self._get_party_cache()
        
        leader = cache['leader']
        members = cache['members']
        
        if not leader or len(members) <= 1:
            return 0
        
        leader.char_base.refresh()
        
        # Проверка: fly_status == 2
        if leader.char_base.fly_status != 2:
            # Размораживаем всех
            for member in members:
                if member.char_base.char_id == leader.char_base.char_id:
                    continue
                
                if member.pid in self.freeze_targets:
                    del self.freeze_targets[member.pid]
                
                member.char_base.set_fly_speed_z(0)
            
            return 0
        
        leader_z = leader.char_base.char_pos_z
        leader_location = leader.char_base.location_id
        
        if leader_z is None or leader_location is None:
            return 0
        
        print(f"\n[FOLLOW] Лидер={leader.char_base.char_name} Z={leader_z:.1f}, Location={leader_location}")

        for member in members:
            # Пропускаем лидера
            if member.char_base.char_id == leader.char_base.char_id:
                continue
            
            member.char_base.refresh()
            
            member_location = member.char_base.location_id
            
            # Проверка локации
            if member_location != leader_location:
                if member.pid in self.freeze_targets:
                    del self.freeze_targets[member.pid]
                print(f"  {member.char_base.char_name} (PID={member.pid}): Location={member_location} (лидер={leader_location}) ❌")
                continue
            
            member_z = member.char_base.char_pos_z
            member_fly_speed = member.char_base.fly_speed
            
            if member_z is None or member_fly_speed is None:
                print(f"  {member.char_base.char_name}: нет данных")
                continue
            
            z_diff = member_z - leader_z
            
            # Если разница > 1м
            if abs(z_diff) > 2.0:
                # Вычисляем значение
                target_speed_z = member_fly_speed if z_diff < 0 else -member_fly_speed
                
                # Добавляем в заморозку
                char_base_addr = member.char_base.cache.get("char_base")
                fly_speed_z_address = char_base_addr + 0x12A8
                
                self.freeze_targets[member.pid] = {
                    'address': fly_speed_z_address,
                    'value': target_speed_z
                }
                
                print(f"  {member.char_base.char_name} (PID={member.pid}): diff={z_diff:+.1f}м → заморожен на {target_speed_z:+.1f} @ {hex(fly_speed_z_address)}")
            else:
                # Убираем из заморозки
                if member.pid in self.freeze_targets:
                    del self.freeze_targets[member.pid]
                
                # Ставим 0
                member.char_base.set_fly_speed_z(0)
                print(f"  {member.char_base.char_name}: OK (diff={z_diff:+.1f}м)")
        
        print(f"  Активных заморозок: {len(self.freeze_targets)}")
        
        return len(self.freeze_targets)
            
    # ===================================================
    # ATTACK (ИСПРАВЛЕНО)
    # ===================================================
    

    def set_attack_target(self):
        """
        Установить таргет лидера всем окнам (ИСПОЛЬЗУЕТ КЕШ)
        
        Обновляет кеш группы каждый тик.
        """
        # ВСЕГДА обновляем кеш
        self._update_party_cache()
        
        cache = self.party_cache
        leader = cache['leader']
        members = cache['members']
        
        if not leader or len(members) <= 1:
            return 0
        
        # Читаем target_id у лидера
        leader.char_base.refresh()
        leader_target_id = leader.char_base.target_id
        
        if not leader_target_id or leader_target_id == 0:
            return 0
        
        # Устанавливаем target_id ВСЕМ окнам (кроме лидера)
        success_count = 0
        
        for char in members:
            # Пропускаем лидера
            if char.pid == leader.pid:
                continue
            
            # Устанавливаем target_id
            if char.char_base.set_target_id(leader_target_id):
                success_count += 1
        
        if success_count > 0:
            logging.info(f"⚔️ Attack: set target {leader_target_id} to {success_count} windows")
        
        return success_count