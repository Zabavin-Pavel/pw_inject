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
    
        # НОВОЕ: Кеш для REDO телепорта
        self.last_teleport_destination = None  # (x, y, z)
    
        # НОВОЕ: Кеш группы (обновляется Attack каждые 500ms)
        self.party_cache = {
            'timestamp': None,
            'leader': None,
            'members': [],
            'member_info': {}
        }

        # НОВОЕ: Кеш для быстрой проверки изменений
        self.quick_check_cache = {
            'pids': set(),           # Текущие PIDs
            'char_ids': {},          # {pid: char_id}
            'party_states': {},      # {pid: party_ptr или 0}
            'timestamp': 0
        }
    
        # НОВОЕ: Единый поток заморозки для Follow
        self.freeze_thread = None
        self.freeze_stop_event = None
        self.freeze_targets = {}

    def needs_refresh(self) -> bool:
        """
        Быстрая проверка - нужен ли refresh?
        
        ВАЖНО: Если ВСЕ окна на выборе персонажа (char_id = 0) - не обновляем
        """
        import time
        
        current_pids = set(self._get_all_pids())
        cached_pids = self.quick_check_cache['pids']
        
        # 1. Проверка PIDs (новые/закрытые окна)
        if current_pids != cached_pids:
            logging.info(f"🔄 PIDs changed: {len(cached_pids)} -> {len(current_pids)}")
            return True
        
        # НОВОЕ: Проверяем что хотя бы одно окно НЕ на выборе персонажа
        from game.offsets import resolve_offset, OFFSETS
        
        has_valid_chars = False
        
        for pid in current_pids:
            if pid not in self.characters:
                continue
            
            char = self.characters[pid]
            
            # Проверка валидности
            if not char.is_valid():
                logging.info(f"🔄 PID {pid} became invalid")
                return True
            
            # Читаем текущий char_id
            char_base = char.char_base.cache.get("char_base")
            if not char_base:
                continue
            
            current_char_id = char.memory.read_int(char_base + 0x6A8)
            
            # Если char_id валиден - есть хотя бы один персонаж в игре
            if current_char_id and current_char_id != 0:
                has_valid_chars = True
            
            # Проверка что char_id не обнулился
            if current_char_id is None or current_char_id == 0:
                cached_char_id = self.quick_check_cache['char_ids'].get(pid)
                if cached_char_id and cached_char_id != 0:
                    logging.info(f"🔄 Char ID became 0 for PID {pid} (character select)")
                    return True
                continue
            
            cached_char_id = self.quick_check_cache['char_ids'].get(pid)
            
            # Проверка смены персонажа
            if current_char_id != cached_char_id:
                if cached_char_id is not None and cached_char_id != 0:
                    logging.info(f"🔄 Char ID changed for PID {pid}: {cached_char_id} -> {current_char_id}")
                    return True
            
            # Читаем текущий party_ptr
            char_origin = char.char_base.cache.get("char_origin")
            if char_origin:
                party_ptr_addr = char_base + 0xAA0
                current_party_ptr = char.memory.read_uint64(party_ptr_addr)
                
                if current_party_ptr is None:
                    continue
                
                cached_party_ptr = self.quick_check_cache['party_states'].get(pid, 0)
                
                # Проверка изменения группы
                if (current_party_ptr == 0) != (cached_party_ptr == 0):
                    logging.info(f"🔄 Party state changed for PID {pid}")
                    return True
        
        # НОВОЕ: Если НЕТ валидных персонажей (все на выборе) - не обновляем
        if not has_valid_chars:
            logging.debug("⏸️ All characters on character select - skip refresh")
            return False
        
        return False

    def update_quick_check_cache(self):
        """Обновить кеш быстрой проверки после refresh"""
        import time
        from game.offsets import resolve_offset, OFFSETS
        
        self.quick_check_cache['pids'] = set(self.characters.keys())
        self.quick_check_cache['char_ids'].clear()
        self.quick_check_cache['party_states'].clear()
        
        for pid, char in self.characters.items():
            if not char.is_valid():
                continue
            
            # НОВОЕ: Безопасная проверка char_id
            char_id = char.char_base.char_id
            if char_id is None or char_id == 0:
                continue
            
            self.quick_check_cache['char_ids'][pid] = char_id
            
            # Кешируем party_ptr
            char_base = char.char_base.cache.get("char_base")
            if char_base:
                try:
                    party_ptr = resolve_offset(
                        char.memory,
                        OFFSETS["party_ptr"],
                        char.char_base.cache
                    )
                    self.quick_check_cache['party_states'][pid] = party_ptr or 0
                except Exception as e:
                    logging.debug(f"Failed to read party_ptr for PID {pid}: {e}")
                    continue
        
        self.quick_check_cache['timestamp'] = time.time()
        logging.debug(f"✅ Quick check cache updated: {len(self.quick_check_cache['pids'])} PIDs")

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
        
        # НОВОЕ: Удаляем персонажей с невалидным char_id (выход на выбор персонажа)
        to_remove = []
        for pid, char in list(self.characters.items()):
            # Быстрая проверка char_id без полного refresh
            char_base = char.char_base.cache.get("char_base")
            if char_base:
                current_char_id = char.memory.read_int(char_base + 0x6A8)
                if current_char_id is None or current_char_id == 0:
                    logging.info(f"🚪 PID {pid} на выборе персонажа, удаляем из списка")
                    to_remove.append(pid)
        
        for pid in to_remove:
            char = self.characters[pid]
            # НЕ закрываем память (процесс еще жив, просто на выборе персонажа)
            del self.characters[pid]
        
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
                # Обновляем fly trigger кеш
                char.update_fly_trigger_cache()
        
        # Пересоздаём персонажей (смена персонажа)
        for pid in to_recreate:
            old_char = self.characters[pid]
            char_base = CharBase(old_char.memory)
            
            # Проверяем валидность перед добавлением
            if not char_base.is_valid():
                logging.warning(f"⚠️ PID {pid} CharBase invalid after recreate, removing")
                del self.characters[pid]
                continue
            
            new_char = Character(pid, old_char.memory, char_base)
            new_char.manager = self
            self.characters[pid] = new_char
            
            char_name = char_base.char_name if char_base.char_name else "???"
            logging.info(f"✅ Character recreated for PID {pid}: {char_name}")
        
        # Добавляем новые процессы
        for pid in current_pids - existing_pids:
            mem = Memory()
            if mem.attach_by_pid(pid):
                char_base = CharBase(mem)

                # ПРОВЕРКА ВАЛИДНОСТИ ДО ДОБАВЛЕНИЯ
                if not char_base.is_valid():
                    logging.warning(f"⚠️ PID {pid} attached but character data is invalid, skipping")
                    mem.close()
                    continue

                logging.info(f"DEBUG PID={pid}: char_origin={hex(char_base.cache.get('char_origin', 0))}, char_base={hex(char_base.cache.get('char_base', 0))}")
                char = Character(pid, mem, char_base)
                char.manager = self
                self.characters[pid] = char
                
                if self._main_pid is None:
                    self._main_pid = pid
                    self.world_manager = WorldManager(mem)
                
                char_name = char_base.char_name if char_base.char_name else "???"
                logging.info(f"✅ New character added: PID={pid}, Name={repr(char_name)}")
        
        # Обновляем мапу pid↔char_id
        if self.app_state:
            self.app_state.update_pid_char_id_map(self.get_all_characters())
            logging.debug(f"🔄 Map updated: {self.app_state.char_id_to_pid}")
        
        # Обновляем кеш быстрой проверки
        self.update_quick_check_cache()
        
        # НОВОЕ: Очищаем last_active_character если он был удален
        if self.app_state and self.app_state.last_active_character:
            active_pid = self.app_state.last_active_character.pid
            if active_pid not in self.characters:
                logging.info(f"🚪 Last active character (PID {active_pid}) removed, clearing")
                self.app_state.last_active_character = None
                
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
        Найти лидера и группу на основе АКТИВНОГО окна
        
        Логика:
        1. Берем активное окно
        2. Если нет группы - возвращаем только его
        3. Если есть группа - возвращаем всех из группы
        
        Returns:
            (leader, group): лидер и список участников
        """
        from game.offsets import resolve_offset, OFFSETS
        
        # Берем активное окно
        active_char = self.app_state.last_active_character if self.app_state else None
        
        # Проверка валидности
        if not active_char or not active_char.is_valid():
            return None, []
        
        # Безопасное обновление
        try:
            active_char.char_base.refresh()
        except:
            if self.app_state:
                self.app_state.last_active_character = None
            return None, []
        
        # Проверка char_id
        if not active_char.char_base.char_id or active_char.char_base.char_id == 0:
            if self.app_state:
                self.app_state.last_active_character = None
            return None, []
        
        active_char_id = active_char.char_base.char_id
        
        # Читаем party_ptr активного персонажа
        party_ptr = resolve_offset(
            active_char.memory,
            OFFSETS["party_ptr"],
            active_char.char_base.cache
        )
        
        # Нет группы - возвращаем только активное окно
        if not party_ptr or party_ptr == 0:
            return active_char, [active_char]
        
        active_char.char_base.cache["party_ptr"] = party_ptr
        
        # Читаем party_leader_id
        party_leader_id = resolve_offset(
            active_char.memory,
            OFFSETS["party_leader_id"],
            active_char.char_base.cache
        )
        
        if not party_leader_id or party_leader_id == 0:
            return active_char, [active_char]
        
        # Собираем всех кто в группе (включая активного)
        all_chars = self.get_all_characters()
        group_members = []
        
        for char in all_chars:
            char.char_base.refresh()
            
            # Читаем party_ptr
            char_party_ptr = resolve_offset(
                char.memory,
                OFFSETS["party_ptr"],
                char.char_base.cache
            )
            
            if not char_party_ptr or char_party_ptr == 0:
                continue
            
            char.char_base.cache["party_ptr"] = char_party_ptr
            
            # Читаем party_leader_id
            char_party_leader_id = resolve_offset(
                char.memory,
                OFFSETS["party_leader_id"],
                char.char_base.cache
            )
            
            # Если лидер совпадает - добавляем в группу
            if char_party_leader_id == party_leader_id:
                group_members.append(char)
        
        # Возвращаем активное окно как "лидера" и всю группу
        return active_char, group_members

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
        import time
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
    # Работает только для окон в пати, с лидером
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
        
        if leader_z is None:
            return 0
        
        print(f"\n[FOLLOW] Лидер={leader.char_base.char_name} Z={leader_z:.1f}")

        for member in members:
            # Пропускаем лидера
            if member.char_base.char_id == leader.char_base.char_id:
                continue
            
            member.char_base.refresh()
            
            member_z = member.char_base.char_pos_z
            member_fly_speed = member.char_base.fly_speed
            
            if member_z is None or member_fly_speed is None:
                print(f"  {member.char_base.char_name}: нет данных")
                continue
            
            z_diff = member_z - leader_z
            
            # Если разница > 1м
            if abs(z_diff) > 2:
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