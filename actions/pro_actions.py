"""
PRO уровень - продвинутые действия с телепортацией
"""
import logging
from core.keygen import PERMISSION_PRO
from config.constants import DUNGEON_POINTS, LONG_LEFT_POINT, LONG_RIGHT_POINT, EXIT_POINT

def register_pro_actions(action_manager, multibox_manager, app_state):
    """
    Зарегистрировать действия уровня PRO
    
    Args:
        action_manager: менеджер действий
        multibox_manager: менеджер мультибокса
        app_state: состояние приложения
    """
    
    # === РАЗДЕЛИТЕЛЬ ===
    action_manager.register(
        'separator_pro',
        label='',  # Пустая строка - визуал через SeparatorRow
        type='quick',
        callback=lambda: None,
        has_hotkey=True,  # Чтобы попал в get_hotkey_actions()
        required_permission=PERMISSION_PRO,
        is_separator=True  # НОВОЕ - это разделитель
    )
    
    # === TARGET ===
    def action_tp_to_target():
        """Телепортировать к таргету (БЕЗ space, БЕЗ проверок)"""
        active_char = app_state.last_active_character
        
        if not active_char:
            print("\n[TP to TARGET] Нет последнего активного окна")
            return
        
        # Вызываем БЕЗ проверок
        multibox_manager.action_teleport_to_target(active_char)
    
    action_manager.register(
        'tp_to_target',
        label='TARGET   [PRO]',
        type='quick',
        callback=action_tp_to_target,
        has_hotkey=True,
        required_permission=PERMISSION_PRO
    )
    
    # === NEXT >> ===
    def action_next():
        """
        Телепортировать группу на следующую точку
        
        Логика:
        1. Проверяем активное окно ИЛИ лидера
        2. Если в триггере любой точки - телепортируем ВСЮ группу
        3. БЕЗ проверки лута, БЕЗ проверки что все в радиусе
        """
        leader, group = multibox_manager.get_leader_and_group()
        active_char = app_state.last_active_character
        
        # Определяем кто проверяется на триггер
        trigger_char = active_char if active_char else leader
        
        if not trigger_char:
            print("\n[NEXT >>] Нет активного окна и нет лидера")
            return
        
        # Получаем позицию персонажа для проверки триггера
        trigger_char.char_base.refresh()
        char_x = trigger_char.char_base.char_pos_x
        char_y = trigger_char.char_base.char_pos_y
        
        if char_x is None or char_y is None:
            print("\n[NEXT >>] Не удалось получить координаты")
            return
        
        # Проверяем все точки
        for point in DUNGEON_POINTS:
            trigger_x, trigger_y = point["trigger"]
            radius = point["radius"]
            
            # Проверка триггера
            dx = abs(char_x - trigger_x)
            dy = abs(char_y - trigger_y)
            
            if dx <= radius and dy <= radius:
                # В триггере! Телепортируем всю группу
                target_x, target_y, target_z = point["target"]
                
                # Получаем всех персонажей группы (или всех если нет группы)
                chars_to_tp = group if group else multibox_manager.get_all_characters()
                
                # Телепортируем (С МАССОВЫМ SPACE)
                success_count = multibox_manager.teleport_group(
                    chars_to_tp,
                    target_x,
                    target_y,
                    target_z,
                    send_space=True
                )
                
                if success_count > 0:
                    print(f"\n[NEXT >>] {point['name']}: телепортировано {success_count} персонажей\n")
                else:
                    print(f"\n[NEXT >>] {point['name']}: никто не был телепортирован\n")
                
                return
        
        print("\n[NEXT >>] Не в триггере ни одной точки\n")
    
    action_manager.register(
        'tp_next',
        label='NEXT >>  [PRO]',
        type='quick',
        callback=action_next,
        has_hotkey=True,
        required_permission=PERMISSION_PRO
    )
    
    # === <- LONG ===
    def action_long_left():
        """Телепортировать к точке LONG LEFT (solo)"""
        _tp_to_special_point("LONG LEFT", LONG_LEFT_POINT, "solo", multibox_manager, app_state)
    
    action_manager.register(
        'tp_long_left',
        label='LONG <-  [PRO]',
        type='quick',
        callback=action_long_left,
        has_hotkey=True,
        required_permission=PERMISSION_PRO
    )
    
    # === LONG -> ===
    def action_long_right():
        """Телепортировать к точке LONG RIGHT (solo)"""
        _tp_to_special_point("LONG RIGHT", LONG_RIGHT_POINT, "solo", multibox_manager, app_state)
    
    action_manager.register(
        'tp_long_right',
        label='LONG ->  [PRO]',
        type='quick',
        callback=action_long_right,
        has_hotkey=True,
        required_permission=PERMISSION_PRO
    )
    
    # === EXIT -> ===
    def action_exit():
        """Телепортировать к точке EXIT (party)"""
        _tp_to_special_point("EXIT", EXIT_POINT, "party", multibox_manager, app_state)
    
    action_manager.register(
        'tp_exit',
        label='EXIT >>  [PRO]',
        type='quick',
        callback=action_exit,
        has_hotkey=True,
        required_permission=PERMISSION_PRO
    )


def _tp_to_special_point(point_name, target_coords, mode, multibox_manager, app_state):
    """
    Универсальная функция телепорта к специальной точке
    
    Args:
        point_name: название точки (для логов)
        target_coords: (x, y, z) координаты
        mode: "solo" или "party"
        multibox_manager: менеджер мультибокса
        app_state: состояние приложения
    """
    target_x, target_y, target_z = target_coords
    
    if mode == "solo":
        # Телепортируем только активное окно (С ОДИНОЧНЫМ SPACE)
        active_char = app_state.last_active_character
        
        if not active_char:
            print(f"\n[{point_name}] Нет активного окна")
            return
        
        success = multibox_manager.teleport_character(
            active_char,
            target_x,
            target_y,
            target_z,
            send_space=True
        )
        
        if success:
            print(f"\n[{point_name}] Телепортирован {active_char.char_base.char_name}\n")
        else:
            print(f"\n[{point_name}] Ошибка телепортации\n")
    
    elif mode == "party":
        # Телепортируем всю группу (С МАССОВЫМ SPACE)
        leader, group = multibox_manager.get_leader_and_group()
        
        if not group:
            print(f"\n[{point_name}] Нет группы")
            return
        
        success_count = multibox_manager.teleport_group(
            group,
            target_x,
            target_y,
            target_z,
            send_space=True
        )
        
        if success_count > 0:
            print(f"\n[{point_name}] Телепортировано {success_count} персонажей\n")
        else:
            print(f"\n[{point_name}] Никто не был телепортирован\n")