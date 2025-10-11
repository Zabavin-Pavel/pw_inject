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