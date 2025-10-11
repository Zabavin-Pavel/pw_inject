"""
Оффсеты для Perfect World
Все оффсеты в одном месте для удобного управления
"""

# CharBase - структура персонажа
CHAR_BASE = {
    "static_path": ["ElementClient.exe+0x013FBB08", 0x68],
    "fields": {
        # Основные данные
        "char_id": 0x6A8,
        "char_class": 0x9D0,
        "char_name_ptr": 0x9C8,
        "level": 0x6B4,
        "target_id": 0x7B4,
        
        # HP/MP
        "hp": 0x6BC,
        "mp": 0x6C0,
        "max_hp": 0x730,
        "max_mp": 0x734,
        
        # Координаты
        "x": 0xA00,
        "y": 0x9F8,
        "z": 0x9FC,
        
        # Направление
        "dir_x": 0x18,
        "dir_y": 0x20,
        
        # Характеристики
        "vitality": 0x720,
        "magic": 0x724,
        "strength": 0x728,
        "dexterity": 0x72C,
    },
    "party": {
        "base_offset": 0xAA0,
        "leader_path": [0x8],  # -> CharBase указатель на лидера
        "count_offset": 0x28,
        "array_offset": 0x20,
        "member_id_offset": 0x18,
        "max_members": 10
    }
}

# WorldManager - окружающий мир
WORLD_MANAGER = {
    "static_path": ["ElementClient.exe+0x0148C338", 0x10],
    "loot": {
        "container_path": [0x28],
        "array_offset": 0x0,
        "count_path": [0x40],  # для счетчика лута
        "item_data_offset": 0x10,
        "x_offset": 0x50,
        "y_offset": 0x48,
        "id_offset": 0x140,
        "max_iterate": 0x1000,
        "step": 0x4
    },
    "people": {
        "container_path": [0x30],
        "array_offset": 0x0,
        "count_path": [0x48],
        "person_data_offset": 0x10,
        "id_offset": 0x6A8,  # такой же как char_id
        "max_iterate": 0x1000,
        "step": 0x4
    },
    "npc": {
        "static_count": "ElementClient.exe+0x01419C7C0",  # статический счетчик
        "container_path": [0x30],  # предполагаемый путь до массива NPC
        "array_offset": 0x0,
        "npc_data_offset": 0x10,
        "id_offset": 0x148,
        "max_iterate": 0x1000,
        "step": 0x4
    }
}

# GameInfo - общая информация
GAME_INFO = {
    "location": {
        "static_path": ["ElementClient.exe+0x0142CDD8", 0x3D8, 0x550],
    },
    "teleport": {
        "static_path": ["ElementClient.exe+0x0149AE10", 0x128, 0x268, 0x50, 0x0],
    }
}

# Для будущего использования
SEND_PACKET = {
    "static_address": 0x009919B0,  # адрес функции SendPacket
}


"""
Проверка оффсетов из offsets.py
Подключается к первому найденному процессу ElementClient.exe
и выводит все значения в консоль
"""
import sys
import ctypes
from memory import Memory
from win32_api import TH32CS_SNAPPROCESS, PROCESSENTRY32
from constants import CLASS_NAMES_DEBUG


def get_first_pid(process_name="ElementClient.exe"):
    """Получить PID первого найденного процесса"""
    kernel32 = ctypes.windll.kernel32
    snapshot = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    pe32 = PROCESSENTRY32()
    pe32.dwSize = ctypes.sizeof(PROCESSENTRY32)
    
    first_pid = None
    
    if kernel32.Process32First(snapshot, ctypes.byref(pe32)):
        while True:
            current_name = pe32.szExeFile.decode('utf-8', errors='ignore')
            if current_name.lower() == process_name.lower():
                first_pid = pe32.th32ProcessID
                break
            
            if not kernel32.Process32Next(snapshot, ctypes.byref(pe32)):
                break
    
    kernel32.CloseHandle(snapshot)
    return first_pid


def resolve_pointer_chain(memory, path):
    """Пройти по цепочке указателей"""
    try:
        current = None
        
        # Первый элемент - статический указатель
        if isinstance(path[0], str) and "+" in path[0]:
            parts = path[0].split("+")
            offset = int(parts[1], 16)
            current = memory.read_uint64(memory.module_base + offset)
            
            if not current:
                return None
        
        # Проходим по цепочке
        for offset in path[1:]:
            if current is None:
                break
            current = memory.read_uint64(current + offset)
            if not current:
                return None
        
        return current
        
    except Exception as e:
        print(f"    ERROR resolving chain: {e}")
        return None


def check_char_base(memory):
    """Проверить CharBase структуру"""
    print("\n" + "="*70)
    print("CHAR BASE")
    print("="*70)
    
    # Резолвим базовый адрес
    base = resolve_pointer_chain(memory, CHAR_BASE["static_path"])
    
    if not base:
        print("❌ Failed to resolve CharBase!")
        return
    
    print(f"✅ CharBase address: {hex(base)}")
    print(f"   Path: {CHAR_BASE['static_path']}")
    print()
    
    # Читаем основные поля
    fields = CHAR_BASE["fields"]
    
    # ID персонажа
    char_id = memory.read_int(base + fields["char_id"])
    print(f"Char ID [{hex(fields['char_id'])}]: {char_id}")
    
    # Класс
    char_class = memory.read_int(base + fields["char_class"])
    class_name = CLASS_NAMES_DEBUG.get(char_class, "Unknown") if char_class is not None else "NULL"
    print(f"Class [{hex(fields['char_class'])}]: {char_class} ({class_name})")
    
    # Имя персонажа
    name_ptr = memory.read_uint64(base + fields["char_name_ptr"])
    if name_ptr:
        char_name = memory.read_string(name_ptr, max_length=30)
        print(f"Name [{hex(fields['char_name_ptr'])}]: '{char_name}'")
    else:
        print(f"Name [{hex(fields['char_name_ptr'])}]: NULL")
    
    # Уровень
    level = memory.read_int(base + fields["level"])
    print(f"Level [{hex(fields['level'])}]: {level}")
    
    # Target ID
    target_id = memory.read_int(base + fields["target_id"])
    print(f"Target ID [{hex(fields['target_id'])}]: {target_id}")
    
    # HP/MP
    hp = memory.read_int(base + fields["hp"])
    max_hp = memory.read_int(base + fields["max_hp"])
    mp = memory.read_int(base + fields["mp"])
    max_mp = memory.read_int(base + fields["max_mp"])
    print(f"HP [{hex(fields['hp'])}]: {hp} / {max_hp}")
    print(f"MP [{hex(fields['mp'])}]: {mp} / {max_mp}")
    
    # Координаты
    x = memory.read_float(base + fields["x"])
    y = memory.read_float(base + fields["y"])
    z = memory.read_float(base + fields["z"])
    print(f"Position:")
    print(f"  X [{hex(fields['x'])}]: {x:.2f}" if x else f"  X [{hex(fields['x'])}]: NULL")
    print(f"  Y [{hex(fields['y'])}]: {y:.2f}" if y else f"  Y [{hex(fields['y'])}]: NULL")
    print(f"  Z [{hex(fields['z'])}]: {z:.2f}" if z else f"  Z [{hex(fields['z'])}]: NULL")
    
    # Направление
    dir_x = memory.read_float(base + fields["dir_x"])
    dir_y = memory.read_float(base + fields["dir_y"])
    print(f"Direction:")
    print(f"  X [{hex(fields['dir_x'])}]: {dir_x:.4f}" if dir_x else f"  X [{hex(fields['dir_x'])}]: NULL")
    print(f"  Y [{hex(fields['dir_y'])}]: {dir_y:.4f}" if dir_y else f"  Y [{hex(fields['dir_y'])}]: NULL")
    
    # Характеристики
    vitality = memory.read_int(base + fields["vitality"])
    magic = memory.read_int(base + fields["magic"])
    strength = memory.read_int(base + fields["strength"])
    dexterity = memory.read_int(base + fields["dexterity"])
    print(f"Stats:")
    print(f"  Vitality [{hex(fields['vitality'])}]: {vitality}")
    print(f"  Magic [{hex(fields['magic'])}]: {magic}")
    print(f"  Strength [{hex(fields['strength'])}]: {strength}")
    print(f"  Dexterity [{hex(fields['dexterity'])}]: {dexterity}")
    
    # Проверка группы
    print("\n--- PARTY INFO ---")
    party_cfg = CHAR_BASE["party"]
    
    party_ptr = memory.read_uint64(base + party_cfg["base_offset"])
    print(f"Party ptr [{hex(party_cfg['base_offset'])}]: {hex(party_ptr) if party_ptr else 'NULL (not in party)'}")
    
    if party_ptr and party_ptr != 0:
        # В группе
        print("✅ Character is in party")
        
        # Лидер
        leader_ptr = memory.read_uint64(party_ptr + party_cfg["leader_path"][0])
        if leader_ptr:
            leader_id = memory.read_int(leader_ptr + fields["char_id"])
            is_leader = (leader_id == char_id)
            print(f"Leader ID [{hex(party_cfg['leader_path'][0])}]: {leader_id} {'(YOU ARE LEADER)' if is_leader else ''}")
        else:
            print(f"Leader ptr [{hex(party_cfg['leader_path'][0])}]: NULL")
        
        # Количество членов
        count = memory.read_int(party_ptr + party_cfg["count_offset"])
        print(f"Party count [{hex(party_cfg['count_offset'])}]: {count}")
        
        # Массив членов
        array_ptr = memory.read_uint64(party_ptr + party_cfg["array_offset"])
        if array_ptr and count and count > 0:
            print(f"Party array [{hex(party_cfg['array_offset'])}]: {hex(array_ptr)}")
            print(f"Party members (max {min(count, party_cfg['max_members'])}):")
            
            for i in range(min(count, party_cfg["max_members"])):
                member_ptr = memory.read_uint64(array_ptr + i * 8)
                if member_ptr:
                    member_id = memory.read_int(member_ptr + party_cfg["member_id_offset"])
                    print(f"  [{i}] ID: {member_id}")
        else:
            print("Party array: NULL or count=0")
    else:
        print("❌ Character is NOT in party")


def check_world_manager(memory):
    """Проверить WorldManager структуру"""
    print("\n" + "="*70)
    print("WORLD MANAGER")
    print("="*70)
    
    # Резолвим базовый адрес
    base = resolve_pointer_chain(memory, WORLD_MANAGER["static_path"])
    
    if not base:
        print("❌ Failed to resolve WorldManager!")
        return
    
    print(f"✅ WorldManager address: {hex(base)}")
    print(f"   Path: {WORLD_MANAGER['static_path']}")
    print()
    
    # Лут
    print("--- LOOT ---")
    loot_cfg = WORLD_MANAGER["loot"]
    loot_container = memory.read_uint64(base + loot_cfg["container_path"][0])
    print(f"Loot container [{hex(loot_cfg['container_path'][0])}]: {hex(loot_container) if loot_container else 'NULL'}")
    
    if loot_container:
        loot_count_ptr = loot_container
        for offset in loot_cfg["count_path"]:
            loot_count_ptr = memory.read_uint64(loot_count_ptr + offset) if loot_count_ptr else None
        
        if loot_count_ptr:
            loot_count = memory.read_int(loot_count_ptr)
            print(f"Loot count: {loot_count if loot_count else 0}")
        
        loot_array = memory.read_uint64(loot_container + loot_cfg["array_offset"])
        print(f"Loot array [{hex(loot_cfg['array_offset'])}]: {hex(loot_array) if loot_array else 'NULL'}")
        
        if loot_array:
            print(f"Scanning first 20 items (step {hex(loot_cfg['step'])}):")
            found = 0
            for i in range(20):
                offset = i * loot_cfg["step"]
                item_ptr = memory.read_uint64(loot_array + offset)
                
                if item_ptr:
                    data_ptr = memory.read_uint64(item_ptr + loot_cfg["item_data_offset"])
                    if data_ptr:
                        item_id = memory.read_int(data_ptr + loot_cfg["id_offset"])
                        x = memory.read_float(data_ptr + loot_cfg["x_offset"])
                        y = memory.read_float(data_ptr + loot_cfg["y_offset"])
                        
                        if item_id and item_id > 0:
                            print(f"  [{i}] ID: {item_id}, pos: ({x:.1f}, {y:.1f})")
                            found += 1
            
            if found == 0:
                print("  No loot items found")
    
    # Игроки
    print("\n--- NEARBY PLAYERS ---")
    people_cfg = WORLD_MANAGER["people"]
    people_container = memory.read_uint64(base + people_cfg["container_path"][0])
    print(f"People container [{hex(people_cfg['container_path'][0])}]: {hex(people_container) if people_container else 'NULL'}")
    
    if people_container:
        people_count_ptr = people_container
        for offset in people_cfg["count_path"]:
            people_count_ptr = memory.read_uint64(people_count_ptr + offset) if people_count_ptr else None
        
        if people_count_ptr:
            people_count = memory.read_int(people_count_ptr)
            print(f"People count: {people_count if people_count else 0}")
        
        people_array = memory.read_uint64(people_container + people_cfg["array_offset"])
        print(f"People array [{hex(people_cfg['array_offset'])}]: {hex(people_array) if people_array else 'NULL'}")
        
        if people_array:
            print(f"Scanning first 20 people (step {hex(people_cfg['step'])}):")
            found = 0
            for i in range(20):
                offset = i * people_cfg["step"]
                person_ptr = memory.read_uint64(people_array + offset)
                
                if person_ptr:
                    data_ptr = memory.read_uint64(person_ptr + people_cfg["person_data_offset"])
                    if data_ptr:
                        player_id = memory.read_int(data_ptr + people_cfg["id_offset"])
                        
                        if player_id and player_id > 0:
                            print(f"  [{i}] Player ID: {player_id}")
                            found += 1
            
            if found == 0:
                print("  No nearby players found")
    
    # NPC
    print("\n--- NPC ---")
    npc_cfg = WORLD_MANAGER["npc"]
    
    # Статический счётчик
    if "+" in npc_cfg["static_count"]:
        parts = npc_cfg["static_count"].split("+")
        offset = int(parts[1], 16)
        npc_count = memory.read_int(memory.module_base + offset)
        print(f"NPC count (static) [{npc_cfg['static_count']}]: {npc_count if npc_count else 0}")


def check_game_info(memory):
    """Проверить GameInfo структуру"""
    print("\n" + "="*70)
    print("GAME INFO")
    print("="*70)
    
    # Location ID
    location_id = resolve_pointer_chain(memory, GAME_INFO["location"]["static_path"])
    print(f"Location ID: {location_id if location_id else 'NULL'}")
    print(f"  Path: {GAME_INFO['location']['static_path']}")
    
    # Teleport ID
    teleport_id = resolve_pointer_chain(memory, GAME_INFO["teleport"]["static_path"])
    print(f"Teleport ID: {teleport_id if teleport_id else 'NULL'}")
    print(f"  Path: {GAME_INFO['teleport']['static_path']}")


def check_send_packet(memory):
    """Проверить адрес SendPacket"""
    print("\n" + "="*70)
    print("SEND PACKET")
    print("="*70)
    
    send_packet_addr = memory.module_base + SEND_PACKET["static_address"]
    print(f"SendPacket function address: {hex(send_packet_addr)}")
    print(f"  Base + {hex(SEND_PACKET['static_address'])} = {hex(send_packet_addr)}")


def main():
    pid = get_first_pid()

    if not pid:
        print("❌ ElementClient.exe not found!")
        print("   Please start the game first.")
        input("\nPress Enter to exit...")
        return
    
    memory = Memory()
    
    if not memory.attach_by_pid(pid):
        print("❌ Failed to attach to process!")
        input("\nPress Enter to exit...")
        return
    
    try:
        # Проверяем все структуры
        check_char_base(memory)
        check_world_manager(memory)
        check_game_info(memory)
        check_send_packet(memory)
        
    except Exception as e:
        print(f"\n❌ ERROR during check: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Закрываем память
        memory.close()
        print("\n✅ Memory handle closed")
    

if __name__ == "__main__":
    main()