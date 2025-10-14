"""
Оффсеты для Perfect World - Path-based формат
Все оффсеты в одном месте с удобной нотацией
"""

OFFSETS = {
    # ========================================
    # CHAR BASE
    # ========================================
    "char_origin": "static:ElementClient.exe +0x013FAB08 +0x1000",
    "char_base": "ptr:char_origin +0x68",
    
    # Структура для движения
    "char_move_struct": "ptr:char_origin +0x50",

    # Основные данные
    "char_id": "int32:char_base +0x6A8",
    "char_class": "int32:char_base +0x9D0",
    "char_name": "str:char_base +0x9C8",
    
    # HP/MP
    "char_hp": "int32:char_base +0x6BC",
    "char_max_hp": "int32:char_base +0x730",
    
    # Координаты
    "char_pos_x": "float:char_base +0xA00",
    "char_pos_y": "float:char_base +0x9F8",
    "char_pos_z": "float:char_base +0x9FC",

    # Полет
    "fly_speed": "float:char_base +0x74C",
    "fly_speed_z": "float:char_base +0x12A8",
    "fly_status": "int32:char_base +0x9DC",
    
    # Группа
    "party_ptr": "ptr:char_base +0xAA0",
    "party_count": "int32:party_ptr +0x28",
    "party_leader_id": "int32:party_ptr +0x8",
    "party_members_array": "ptr:party_ptr +0x20",
    "party_members": "array:party_members_array:10:8:{id:int32:0x18}",
    
    # ========================================
    # WORLD MANAGER
    # ========================================
    "world_origin": "static:ElementClient.exe +0x0148C338 +0x1000",
    "world_base": "ptr:world_origin +0x10",
    
    # Лут
    "loot_count": "int32:world_base +0x40",
    "loot_container": "ptr:world_base +0x28",
    "loot_items": "array:loot_container:4096:4:{x:float:0x10->0x50,y:float:0x10->0x48}",
    
    # Люди
    "people_count": "int32:world_origin +0x0 -> +0x48",
    "people_container": "ptr:world_base +0x28",
    "people_items": "array:people_container:4096:4:{id:uint32:0x10->0x6A8,x:float:0x10->0x50,y:float:0x10->0x48,z:float:0x10->0x4C}",
    
    # ========================================
    # SELECTION MANAGER (Target + Movepoint)
    # ========================================
    "selection_origin": "static:ElementClient.exe +0x013FBB40",  # БЕЗ +0x1000!
    "selection_ptr": "ptr:selection_origin +0x58 -> +0x0",

    # Target (выбранная цель)
    "target_id": "uint32:char_base +0x7B4",  # ID выбранной цели
    "target_ptr": "ptr:selection_ptr +0x0 -> +0x10",
    "target_pos_x": "float:target_ptr +0xFC",
    "target_pos_y": "float:target_ptr +0xF4",
    "target_pos_z": "float:target_ptr +0xF8",

    # ========================================
    # GAME INFO
    # ========================================
    "location_origin": "static:ElementClient.exe +0x0149AE10 +0x1000",
    "location_id": "int32:location_origin -> +0x0 -> +0x50 -> +0x268 -> +0x128 -> +0x10",
}



import ctypes
from collections import Counter
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

def parse_array_fields(fields_str):
    """
    Парсит строку полей массива
    Формат: {field1:type1:offset1,field2:type2:offset2}
    Поддерживает цепочки: {x:float:0x10->0x50}
    Возвращает: [(field_name, type, offset_chain), ...]
    где offset_chain - это список оффсетов для перехода по указателям
    """
    if not fields_str.startswith("{") or not fields_str.endswith("}"):
        return []
    
    fields_str = fields_str[1:-1]  # Убираем { }
    fields = []
    
    for field_def in fields_str.split(","):
        parts = field_def.split(":")
        if len(parts) == 3:
            field_name = parts[0].strip()
            field_type = parts[1].strip()
            offset_path = parts[2].strip()
            
            # Парсим цепочку оффсетов (поддержка ->)
            if "->" in offset_path:
                offset_chain = []
                for offset_str in offset_path.split("->"):
                    offset_str = offset_str.strip()
                    offset = int(offset_str, 16) if offset_str.startswith("0x") else int(offset_str)
                    offset_chain.append(offset)
            else:
                offset = int(offset_path, 16) if offset_path.startswith("0x") else int(offset_path)
                offset_chain = [offset]
            
            fields.append((field_name, field_type, offset_chain))
    
    return fields

def resolve_offset(memory, path_str, cached_values=None):
    """
    Парсит path-based оффсет и возвращает финальное значение
    
    Формат массива: array:base_ref:max_count:step:{field1:type1:offset1,...}
    Пример: "array:party_members_array:10:8:{id:int32:0x18}"
    """
    if cached_values is None:
        cached_values = {}
    
    # Проверка на массив
    if path_str.startswith("array:"):
        # Парсим формат array:base_ref:max_count:step:{fields}
        brace_pos = path_str.find("{")
        if brace_pos == -1:
            return []
        
        # Парсим параметры до скобки
        params_part = path_str[6:brace_pos]  # Убираем "array:"
        params = params_part.split(":")
        
        if len(params) < 3:
            return []
        
        base_ref = params[0]
        max_count = int(params[1])
        step = int(params[2])
        
        # Парсим поля
        fields_str = path_str[brace_pos:]
        fields = parse_array_fields(fields_str)
        
        if not fields:
            return []
        
        # Получаем базовый адрес массива
        if base_ref in cached_values:
            array_base = cached_values[base_ref]
        elif base_ref in OFFSETS:
            array_base = resolve_offset(memory, OFFSETS[base_ref], cached_values)
        else:
            return []
        
        if not array_base:
            return []
        
        # Собираем ВСЕ указатели и считаем сколько раз каждый встречается
        all_ptrs = []
        
        for i in range(max_count):
            element_ptr = memory.read_uint64(array_base + i * step)
            if element_ptr:
                all_ptrs.append(element_ptr)
        
        # Считаем количество вхождений каждого указателя
        ptr_counter = Counter(all_ptrs)
        
        # Берём только указатели которые встречаются ОДИН раз
        unique_ptrs = [ptr for ptr, count in ptr_counter.items() if count == 1]
        
        # В resolve_offset, в части обработки массивов, заменить на:

        # Для каждого уникального указателя читаем все поля
        results = []

        for ptr in unique_ptrs:
            item = {}
            
            for field_name, field_type, offset_chain in fields:
                # Проходим по цепочке указателей
                current_ptr = ptr
                
                # Идем по цепочке, читая указатели на каждом шаге кроме последнего
                for i, offset in enumerate(offset_chain):
                    current_ptr = current_ptr + offset
                    
                    # Если это не последний элемент - читаем указатель
                    if i < len(offset_chain) - 1:
                        current_ptr = memory.read_uint64(current_ptr)
                        if not current_ptr:
                            break
                
                # Если дошли до конца цепочки - читаем финальное значение
                if current_ptr:
                    if field_type == "int32":
                        value = memory.read_int(current_ptr)
                    elif field_type == "uint32":
                        value = memory.read_uint(current_ptr)
                    elif field_type == "float":
                        value = memory.read_float(current_ptr)
                    else:
                        value = None
                else:
                    value = None
                
                item[field_name] = value
            
            # Фильтрация для координат (только если есть поля x/y)
            # Для других массивов (party) - добавляем если есть ненулевые значения
            if any(v is not None and v != 0 for v in item.values()):
                results.append(item)

        return results
    
    # Обычная обработка
    parts = path_str.split()
    data_type = None
    current_addr = 0
    
    i = 0
    while i < len(parts):
        part = parts[i]
        
        # Определяем тип данных и ссылку
        if ":" in part:
            type_and_ref = part.split(":", 1)
            data_type = type_and_ref[0]
            ref = type_and_ref[1] if len(type_and_ref) > 1 else None
            
            if data_type == "static":
                current_addr = memory.module_base
                i += 1
                continue
                
            elif data_type in ["ptr", "int32", "uint32", "float", "str"]:
                if ref and ref in cached_values:
                    current_addr = cached_values[ref]
                elif ref and ref in OFFSETS:
                    current_addr = resolve_offset(memory, OFFSETS[ref], cached_values)
                    if current_addr is None:
                        return None
                i += 1
                continue
        
        elif part.startswith("+0x"):
            offset = int(part[1:], 16)
            current_addr += offset
            
            # Проверяем следующий элемент - если это "->" то читаем указатель
            if i + 1 < len(parts) and parts[i + 1] == "->":
                current_addr = memory.read_uint64(current_addr)
                if not current_addr:
                    return None
                i += 1  # Пропускаем "->"
        
        elif part == "ElementClient.exe":
            pass
        
        elif part == "->":
            pass
        
        i += 1
    
    # Читаем финальное значение по типу
    if data_type == "static":
        return memory.read_uint64(current_addr)
    elif data_type == "ptr":
        return memory.read_uint64(current_addr)
    elif data_type == "int32":
        return memory.read_int(current_addr)
    elif data_type == "uint32":
        return memory.read_uint(current_addr)
    elif data_type == "float":
        return memory.read_float(current_addr)
    elif data_type == "str":
        max_len = 32
        ptr = memory.read_uint64(current_addr)
        if ptr:
            return memory.read_string(ptr, max_length=max_len)
        return None
    else:
        return current_addr

def main():
    print("="*70)
    print("ПРОВЕРКА ВСЕХ ОФФСЕТОВ")
    print("="*70)
    
    pid = get_first_pid()
    
    if not pid:
        print("❌ ElementClient.exe не найден!")
        return
    
    print(f"✅ Найден процесс PID: {pid}")
    
    memory = Memory()
    
    if not memory.attach_by_pid(pid):
        print("❌ Не удалось подключиться к процессу!")
        return
    
    print(f"✅ Подключено к процессу, base: {hex(memory.module_base)}")
    
    try:
        cache = {}
        
        # ========================================
        # CHAR BASE
        # ========================================
        print("="*70)
        print("CHAR BASE")
        print("="*70)
        
        char_origin = resolve_offset(memory, OFFSETS["char_origin"], cache)
        if char_origin:
            cache["char_origin"] = char_origin
            print(f"✅ char_origin: {hex(char_origin)}")
        else:
            print("❌ char_origin: NULL")
            return
        
        char_base = resolve_offset(memory, OFFSETS["char_base"], cache)
        if char_base:
            cache["char_base"] = char_base
            print(f"✅ char_base: {hex(char_base)}")
        else:
            print("❌ char_base: NULL")
            return
        
        # Основные данные
        char_id = resolve_offset(memory, OFFSETS["char_id"], cache)
        print(f"Char ID: {char_id}")
        
        char_class = resolve_offset(memory, OFFSETS["char_class"], cache)
        class_name = CLASS_NAMES_DEBUG.get(char_class, "Unknown") if char_class is not None else "NULL"
        print(f"Class: {char_class} ({class_name})")
        
        char_name = resolve_offset(memory, OFFSETS["char_name"], cache)
        print(f"Name: '{char_name}'")
        
        target_id = resolve_offset(memory, OFFSETS["target_id"], cache)
        print(f"Target ID: {target_id}")
        
        # HP/MP
        hp = resolve_offset(memory, OFFSETS["char_hp"], cache)
        max_hp = resolve_offset(memory, OFFSETS["char_max_hp"], cache)
        print(f"HP: {hp} / {max_hp}")
        
        # Координаты
        x = resolve_offset(memory, OFFSETS["char_pos_x"], cache)
        y = resolve_offset(memory, OFFSETS["char_pos_y"], cache)
        z = resolve_offset(memory, OFFSETS["char_pos_z"], cache)
        print(f"Position: X={x:.2f}, Y={y:.2f}, Z={z:.2f}")
        
        # ========================================
        # PARTY
        # ========================================
        print("="*70)
        print("PARTY INFO")
        print("="*70)
        
        party_ptr = resolve_offset(memory, OFFSETS["party_ptr"], cache)
        if party_ptr:
            cache["party_ptr"] = party_ptr
            print(f"✅ In party, party_ptr: {hex(party_ptr)}")
            
            party_count = resolve_offset(memory, OFFSETS["party_count"], cache)
            print(f"Party count: {party_count}")
            
            party_leader_id = resolve_offset(memory, OFFSETS["party_leader_id"], cache)
            is_leader = (party_leader_id == char_id)
            print(f"Leader ID: {party_leader_id} {'(YOU ARE LEADER)' if is_leader else ''}")
            
            # Массив участников
            party_members_array = resolve_offset(memory, OFFSETS["party_members_array"], cache)
            if party_members_array:
                cache["party_members_array"] = party_members_array
                members = resolve_offset(memory, OFFSETS["party_members"], cache)
                if members:
                    print(f"Party members ({len(members)}):")
                    for member in members:
                        print(f"  ID: {member['id']}")
                else:
                    print("Party members: []")
        else:
            print("❌ NOT in party")
        
        # ========================================
        # WORLD MANAGER
        # ========================================
        print("="*70)
        print("WORLD MANAGER")
        print("="*70)
        
        world_origin = resolve_offset(memory, OFFSETS["world_origin"], cache)
        if world_origin:
            cache["world_origin"] = world_origin
            print(f"✅ world_origin: {hex(world_origin)}")
        else:
            print("❌ world_origin: NULL")
        
        world_base = resolve_offset(memory, OFFSETS["world_base"], cache)
        if world_base:
            cache["world_base"] = world_base
            print(f"✅ world_base: {hex(world_base)}")
        else:
            print("❌ world_base: NULL")
        
        # Лут
        loot_container = resolve_offset(memory, OFFSETS["loot_container"], cache)
        if loot_container:
            cache["loot_container"] = loot_container
            print(f"✅ loot_container: {hex(loot_container)}")
            
            loot_count = resolve_offset(memory, OFFSETS["loot_count"], cache)
            print(f"Loot count: {loot_count}")
            
            # Получаем все предметы лута (без фильтрации по расстоянию)
            loot_items_raw = resolve_offset(memory, OFFSETS["loot_items"], cache)
            
            # Фильтруем по расстоянию от персонажа
            loot_items = []
            if loot_items_raw:
                for item in loot_items_raw:
                    loot_x = item.get('x')
                    loot_y = item.get('y')
                    
                    if loot_x is not None and loot_y is not None:
                        # Проверяем расстояние от персонажа
                        dx = abs(loot_x - x)
                        dy = abs(loot_y - y)
                        
                        # Лут должен быть в радиусе 50 метров по X и Y
                        if dx <= 50 and dy <= 50:
                            loot_items.append(item)
            
            if loot_items:
                print(f"Loot items nearby ({len(loot_items)}):")
                for item in loot_items:
                    print(item)
            else:
                print("Loot items nearby: []")
        else:
            print("Loot container: NULL")
        
        # Лут
        people_container = resolve_offset(memory, OFFSETS["people_container"], cache)
        if people_container:
            cache["people_container"] = people_container
            print(f"✅ people_container: {hex(people_container)}")
            
            people_count = resolve_offset(memory, OFFSETS["people_count"], cache)
            print(f"people count: {people_count}")
            
            # Получаем все предметы лута (без фильтрации по расстоянию)
            people_items_raw = resolve_offset(memory, OFFSETS["people_items"], cache)

            # Фильтруем по расстоянию от персонажа
            people_items = []
            if people_items_raw:
                for item in people_items_raw:
                    people_id = item.get('id')

                    if people_id is not None and people_id > 1:
                        people_items.append(item)
            
            if people_items:
                print(f"people nearby ({len(people_items)}):")
                for item in people_items:
                    print(item)
            else:
                print("people nearby: []")
        else:
            print("people container: NULL")
                    
        # ========================================
        # GAME INFO
        # ========================================
        print("="*70)
        print("GAME INFO")
        print("="*70)
        
        location_origin = resolve_offset(memory, OFFSETS["location_origin"], cache)
        if location_origin:
            cache["location_origin"] = location_origin
            print(f"✅ location_origin: {hex(location_origin)}")
        
        location_id = resolve_offset(memory, OFFSETS["location_id"], cache)
        print(f"Location ID: {location_id}")
        
        # ========================================
        # SELECTION MANAGER TEST
        # ========================================
        print("="*70)
        print("SELECTION MANAGER (Target + Movepoint)")
        print("="*70)

        selection_origin = resolve_offset(memory, OFFSETS["selection_origin"], cache)
        if selection_origin:
            cache["selection_origin"] = selection_origin
            print(f"✅ selection_origin: {hex(selection_origin)}")

        selection_ptr = resolve_offset(memory, OFFSETS["selection_ptr"], cache)
        if selection_ptr:
            cache["selection_ptr"] = selection_ptr
            print(f"✅ selection_ptr: {hex(selection_ptr)}")
            
            # TARGET
            print("\n--- TARGET ---")
            if target_id and target_id != 0:
                target_ptr = resolve_offset(memory, OFFSETS["target_ptr"], cache)
                if target_ptr:
                    cache["target_ptr"] = target_ptr
                    print(f"✅ target_ptr: {hex(target_ptr)}")
                    
                    t_x = resolve_offset(memory, OFFSETS["target_pos_x"], cache)
                    t_y = resolve_offset(memory, OFFSETS["target_pos_y"], cache)
                    t_z = resolve_offset(memory, OFFSETS["target_pos_z"], cache)
                    
                    if t_x is not None and t_y is not None and t_z is not None:
                        print(f"Target Position: X={t_x:.2f}, Y={t_y:.2f}, Z={t_z:.2f}")
                        
                        if x is not None and y is not None and z is not None:
                            import math
                            distance = math.sqrt((t_x - x)**2 + (t_y - y)**2 + (t_z - z)**2)
                            print(f"Distance to target: {distance:.2f}m")
                else:
                    print("❌ target_ptr: NULL")
            else:
                print("No target selected")

        # ========================================
        # TEST FREEZE MECHANISM
        # ========================================
        # if char_base and x is not None:
        #     print("="*70)
        #     print("READY TO TEST FREEZE MECHANISM")
        #     print("="*70)
            
        #     test_freeze_hp(memory, char_base)


    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        memory.close()
        print("✅ Память закрыта")

    
if __name__ == '__main__':
    main()