"""
PRO уровень - продвинутые действия с телепортацией
"""
import logging
from core.keygen import PERMISSION_PRO, PERMISSION_DEV
from config.constants import (
    DUNGEON_POINTS, 
    LONG_LEFT_POINT, 
    LONG_RIGHT_POINT, 
    EXIT_POINT,
    MAIN_POINT
)

def get_point_type(point_name: str) -> str:
    """
    Определить тип точки по имени
    
    Args:
        point_name: название точки
    
    Returns:
        "FROST", "QB" или None
    """
    if "FROST" in point_name:
        return "FROST"
    elif "QB" in point_name:
        return "QB"
    return None


def can_use_point(point_name: str, permission_level: str) -> bool:
    """
    Проверить доступность точки для уровня доступа
    
    Args:
        point_name: название точки
        permission_level: "try", "pro", "dev"
    
    Returns:
        bool: True если точка доступна
    """
    point_type = get_point_type(point_name)
    
    if permission_level == "dev":
        return True  # DEV видит ВСЕ точки
    elif permission_level == "pro":
        return point_type in "FROST"  # PRO только FROST
    elif permission_level == "try":
        return False  # TRY не видит точки
    
    return False


def register_pro_actions(action_manager, multibox_manager, app_state, action_limiter):
    """
    Зарегистрировать действия уровня PRO
    
    Args:
        action_manager: менеджер действий
        multibox_manager: менеджер мультибокса
        app_state: состояние приложения
        action_limiter: система лимитов
    """
    
    # === РАЗДЕЛИТЕЛЬ ===
    action_manager.register(
        'separator_pro',
        label='',
        type='quick',
        callback=lambda: None,
        has_hotkey=True,
        required_permission=PERMISSION_PRO,
        is_separator=True
    )
    
    # # === TARGET ===
    # def action_tp_to_target():
    #     """Телепортировать к таргету (БЕЗ space, С ПРОВЕРКОЙ ЛОКАЦИИ)"""
    #     active_char = app_state.last_active_character
        
    #     if not active_char:
    #         print("\n[TP to TARGET] Нет последнего активного окна")
    #         return
          
    #     multibox_manager.action_teleport_to_target(active_char)
    
    # action_manager.register(
    #     'tp_to_target',
    #     label='TARGET   [PRO]',
    #     type='quick',
    #     callback=action_tp_to_target,
    #     has_hotkey=True,
    #     required_permission=PERMISSION_PRO
    # )
    
    # === NEXT >> (ОБНОВЛЕНО: поддержка FROST и QB точек) ===
    def action_next():
        """
        Телепортировать группу на следующую точку
        
        Логика:
        1. Берем активного персонажа
        2. Проверяем доступные точки по permission
        3. Проверяем триггер-зоны
        4. Телепортируем группу (или соло как группу из 1)
        5. Записываем точку в кеш для REDO
        6. Записываем лимиты по типу точки
        """
        active_char = app_state.last_active_character
        
        if not active_char:
            print("\n[NEXT >>] Нет активного окна")
            return
        
        # Обновляем координаты активного персонажа
        active_char.char_base.refresh()
        
        char_x = active_char.char_base.char_pos_x
        char_y = active_char.char_base.char_pos_y
        char_z = active_char.char_base.char_pos_z
        
        if char_x is None or char_y is None:
            print("\n[NEXT >>] Не удалось прочитать координаты")
            return
        
        # Получаем уровень доступа
        permission = app_state.permission_level
        
        # Проверяем все точки
        for point in DUNGEON_POINTS:
            # Проверяем доступность точки по permission
            if not can_use_point(point['name'], permission):
                continue
            
            trigger_x, trigger_y = point['trigger']
            radius = point.get('radius', 15.0)
            count_in_limits = point.get('count_in_limits', True)
            
            # Дистанция до триггера (только X и Y)
            dx = abs(char_x - trigger_x)
            dy = abs(char_y - trigger_y)
            
            if dx <= radius and dy <= radius:
                # НАШЛИ ТРИГГЕР-ЗОНУ!
                print(f"\n[NEXT >>] В триггер-зоне точки: {point['name']}")
                print(f"  Текущие координаты: X={char_x:.1f}, Y={char_y:.1f}, Z={char_z:.1f}")
                print(f"  Триггер: X={trigger_x}, Y={trigger_y}, радиус={radius}")
                
                # Определяем тип точки
                point_type = get_point_type(point['name'])
                
                if not point_type:
                    print(f"\n[NEXT >>] Неизвестный тип точки: {point['name']}")
                    print(f"  Текущие координаты: X={char_x:.1f}, Y={char_y:.1f}, Z={char_z:.1f}")
                    return
                
                # ПРОВЕРКА ЛИМИТА для данного типа
                if count_in_limits and not action_limiter.can_use(point_type):
                    print(f"\n[NEXT >>] ⛔ Лимит {point_type} достигнут")
                    return
                
                target_x, target_y, target_z = point['target']
                
                print(f"  Целевые координаты: X={target_x}, Y={target_y}, Z={target_z}")
                
                # СОХРАНЯЕМ ТОЧКУ ДЛЯ REDO
                multibox_manager.last_teleport_destination = (target_x, target_y, target_z)
                
                # Получаем группу (всегда работаем с группой, даже если она из 1 человека)
                _, group = multibox_manager.get_leader_and_group()
                
                if not group:
                    print(f"\n[NEXT >>] Нет группы")
                    return
                
                # ГРУППОВОЙ ТЕЛЕПОРТ
                success_count = multibox_manager.teleport_group(
                    group,
                    target_x,
                    target_y,
                    target_z,
                    send_space=True
                )
                
                if success_count > 0:
                    print(f"\n[NEXT >>] {point['name']}: телепортировано {success_count} персонажей\n")
                    
                    # Записываем использование по типу точки
                    if count_in_limits:
                        action_limiter.record_usage(point_type)
                else:
                    print(f"\n[NEXT >>] {point['name']}: никто не был телепортирован\n")
                
                return
        
        print(f"\n[NEXT >>] Не в триггере ни одной точки")
        print(f"  Текущие координаты: X={char_x:.1f}, Y={char_y:.1f}, Z={char_z:.1f}\n")
    
    action_manager.register(
        'tp_next',
        # label='NEXT >>  [PRO]',
        label='JUMP >>  [PRO]',
        type='quick',
        callback=action_next,
        has_hotkey=True,
        required_permission=PERMISSION_PRO
    )
    
    # # === <- LONG ===
    # def action_long_left():
    #     """Телепортировать к точке LONG LEFT (НЕ расходует лимиты)"""
    #     _tp_to_special_point("LONG LEFT", LONG_LEFT_POINT, "solo", multibox_manager, app_state)
    
    # action_manager.register(
    #     'tp_long_left',
    #     label='LONG <-  [PRO]',
    #     type='quick',
    #     callback=action_long_left,
    #     has_hotkey=True,
    #     required_permission=PERMISSION_PRO
    # )
    
    # # === LONG -> ===
    # def action_long_right():
    #     """Телепортировать к точке LONG RIGHT (НЕ расходует лимиты)"""
    #     _tp_to_special_point("LONG RIGHT", LONG_RIGHT_POINT, "solo", multibox_manager, app_state)
    
    # action_manager.register(
    #     'tp_long_right',
    #     label='LONG ->  [PRO]',
    #     type='quick',
    #     callback=action_long_right,
    #     has_hotkey=True,
    #     required_permission=PERMISSION_PRO
    # )
    
    # # === MAIN <> ===
    # def action_main():
    #     """Телепортировать к точке LONG RIGHT (НЕ расходует лимиты)"""
    #     _tp_to_special_point("LONG RIGHT", MAIN_POINT, "solo", multibox_manager, app_state)
    
    # action_manager.register(
    #     'tp_main',
    #     label='MAIN <>  [PRO]',
    #     type='quick',
    #     callback=action_main,
    #     has_hotkey=True,
    #     required_permission=PERMISSION_PRO
    # )
    
    # === REDO >> (ВМЕСТО EXIT) ===
    def action_redo():
        """Телепортировать на последнюю сохраненную точку из NEXT (НЕ расходует лимиты)"""
        if not multibox_manager.last_teleport_destination:
            print("\n[REDO >>] Нет сохраненной точки для REDO телепорта\n")
            return
        
        target_x, target_y, target_z = multibox_manager.last_teleport_destination
        
        # Получаем группу (всегда работаем с группой)
        _, group = multibox_manager.get_leader_and_group()
        
        if not group:
            print(f"\n[REDO >>] Нет группы")
            return
        
        # ГРУППОВОЙ ТЕЛЕПОРТ (НЕ ЗАПИСЫВАЕМ ЛИМИТЫ!)
        success_count = multibox_manager.teleport_group(
            group,
            target_x,
            target_y,
            target_z,
            send_space=True
        )
        
        if success_count > 0:
            print(f"\n[REDO >>] Телепортировано {success_count} персонажей\n")
        else:
            print(f"\n[REDO >>] Никто не был телепортирован\n")
    
    action_manager.register(
        'tp_redo',
        label='REDO >>  [PRO]',
        type='quick',
        callback=action_redo,
        has_hotkey=True,
        required_permission=PERMISSION_PRO
    )


# def _tp_to_special_point(point_name, point_data, mode, multibox_manager, app_state):
#     """
#     Универсальная функция телепорта к специальной точке (С ОДИНОЧНЫМ SPACE)
    
#     Args:
#         point_name: название точки (для логов)
#         point_data: (x, y, z)
#         mode: "solo" (всегда соло для LONG точек)
#         multibox_manager: менеджер мультибокса
#         app_state: состояние приложения
#     """
#     target_x, target_y, target_z = point_data
    
#     # Телепортируем только активное окно (С ОДИНОЧНЫМ SPACE)
#     active_char = app_state.last_active_character
    
#     if not active_char:
#         print(f"\n[{point_name}] Нет активного окна")
#         return
    
#     success = multibox_manager.teleport_character(
#         active_char,
#         target_x,
#         target_y,
#         target_z,
#         send_space=True
#     )
    
#     if success:
#         print(f"\n[{point_name}] Телепортирован {active_char.char_base.char_name}\n")
#     else:
#         print(f"\n[{point_name}] Ошибка телепортации\n")