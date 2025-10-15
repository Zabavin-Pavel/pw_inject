"""
PRO уровень - продвинутые действия с телепортацией
ОБНОВЛЕНО: упрощен NEXT, добавлены лимиты
"""
import logging
from core.keygen import PERMISSION_PRO
from config.constants import DUNGEON_POINTS, LONG_LEFT_POINT, LONG_RIGHT_POINT, EXIT_POINT

def register_pro_actions(action_manager, multibox_manager, app_state, action_limiter):
    """
    Зарегистрировать действия уровня PRO
    
    Args:
        action_manager: менеджер действий
        multibox_manager: менеджер мультибокса
        app_state: состояние приложения
        action_limiter: система лимитов (НОВОЕ)
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
    
    # === TARGET ===
    def action_tp_to_target():
        """Телепортировать к таргету (БЕЗ space, БЕЗ проверок)"""
        active_char = app_state.last_active_character
        
        if not active_char:
            print("\n[TP to TARGET] Нет последнего активного окна")
            return
        
        multibox_manager.action_teleport_to_target(active_char)
    
    action_manager.register(
        'tp_to_target',
        label='TARGET   [PRO]',
        type='quick',
        callback=action_tp_to_target,
        has_hotkey=True,
        required_permission=PERMISSION_PRO
    )
    
    # === NEXT >> (УПРОЩЕНО) ===
    def action_next():
        """
        Телепортировать группу на следующую точку (УПРОЩЕНО)
        
        Новая логика:
        1. Берем активного персонажа
        2. Если нет пати - одиночный прыжок
        3. Если есть пати - групповой с проверкой локации
        """
        # ПРОВЕРКА ЛИМИТА (быстро, из кеша)
        if not action_limiter.can_use('tp_next'):
            print("\n[NEXT >>] ⛔ Лимит использований достигнут")
            return
        
        # Берем активного персонажа
        active_char = app_state.last_active_character
        
        if not active_char:
            print("\n[NEXT >>] Нет активного окна")
            return
        
        # Обновляем данные
        active_char.char_base.refresh()
        char_x = active_char.char_base.char_pos_x
        char_y = active_char.char_base.char_pos_y
        char_location = active_char.char_base.location_id
        
        if char_x is None or char_y is None or char_location is None:
            print("\n[NEXT >>] Не удалось получить координаты/локацию")
            return
        
        # Проверяем триггеры всех точек
        for point in DUNGEON_POINTS:
            trigger_x, trigger_y = point["trigger"]
            radius = point["radius"]
            
            dx = abs(char_x - trigger_x)
            dy = abs(char_y - trigger_y)
            
            if dx <= radius and dy <= radius:
                # В триггере! Телепортируем
                target_x, target_y, target_z = point["target"]
                
                # Проверяем есть ли пати
                from game.offsets import resolve_offset, OFFSETS
                party_ptr = resolve_offset(
                    active_char.memory, 
                    OFFSETS["party_ptr"], 
                    active_char.char_base.cache
                )
                
                if not party_ptr or party_ptr == 0:
                    # НЕТ ПАТИ - одиночный телепорт
                    success = multibox_manager.teleport_character(
                        active_char,
                        target_x,
                        target_y,
                        target_z,
                        send_space=True
                    )
                    
                    if success:
                        print(f"\n[NEXT >>] {point['name']}: телепортирован {active_char.char_base.char_name}\n")
                        # Записываем использование
                        action_limiter.record_usage('tp_next')
                    else:
                        print(f"\n[NEXT >>] {point['name']}: ошибка телепортации\n")
                else:
                    # ЕСТЬ ПАТИ - групповой телепорт с проверкой локации
                    _, group = multibox_manager.get_leader_and_group()
                    
                    # Фильтруем по локации
                    chars_to_tp = []
                    for member in group:
                        member.char_base.refresh()
                        member_location = member.char_base.location_id
                        
                        if member_location == char_location:
                            chars_to_tp.append(member)
                    
                    if chars_to_tp:
                        success_count = multibox_manager.teleport_group(
                            chars_to_tp,
                            target_x,
                            target_y,
                            target_z,
                            send_space=True
                        )
                        
                        if success_count > 0:
                            print(f"\n[NEXT >>] {point['name']}: телепортировано {success_count} персонажей\n")
                            # Записываем использование
                            action_limiter.record_usage('tp_next')
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
        # ПРОВЕРКА ЛИМИТА
        if not action_limiter.can_use('tp_long_left'):
            print("\n[LONG <-] ⛔ Лимит использований достигнут")
            return
        
        _tp_to_special_point("LONG LEFT", LONG_LEFT_POINT, "solo", multibox_manager, app_state)
        
        # Записываем использование
        action_limiter.record_usage('tp_long_left')
    
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
        # ПРОВЕРКА ЛИМИТА
        if not action_limiter.can_use('tp_long_right'):
            print("\n[LONG ->] ⛔ Лимит использований достигнут")
            return
        
        _tp_to_special_point("LONG RIGHT", LONG_RIGHT_POINT, "solo", multibox_manager, app_state)
        
        # Записываем использование
        action_limiter.record_usage('tp_long_right')
    
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
        # ПРОВЕРКА ЛИМИТА
        if not action_limiter.can_use('tp_exit'):
            print("\n[EXIT >>] ⛔ Лимит использований достигнут")
            return
        
        _tp_to_special_point("EXIT", EXIT_POINT, "party", multibox_manager, app_state)
        
        # Записываем использование
        action_limiter.record_usage('tp_exit')
    
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