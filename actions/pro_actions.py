"""
PRO уровень - продвинутые действия с телепортацией
"""
import logging
from core.keygen import PERMISSION_PRO, PERMISSION_DEV
from config.constants import (
    DUNGEON_POINTS, 
    LONG_LEFT_POINT, 
    LONG_RIGHT_POINT, 
    EXIT_POINT
)

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
    
    # === TARGET ===
    def action_tp_to_target():
        """Телепортировать к таргету (БЕЗ space)"""
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
    
    # === NEXT >> - ОБНОВЛЯЕМ для сохранения точки в кеш ===
    def action_next():
        """
        Телепортировать группу на следующую точку
        
        Логика:
        1. Берем активного персонажа
        2. Проверяем триггер-зоны точек
        3. Если нет пати - одиночный прыжок
        4. Если есть пати - групповой прыжок
        5. ЗАПИСЫВАЕМ ТОЧКУ В КЕШ для REDO
        """
        # ПРОВЕРКА ЛИМИТА
        if not action_limiter.can_use('tp_next'):
            print("\n[NEXT >>] ⛔ Лимит использований достигнут")
            return
        
        active_char = app_state.last_active_character
        
        if not active_char:
            print("\n[NEXT >>] Нет активного окна")
            return
        
        # Обновляем координаты активного персонажа
        active_char.char_base.refresh()
        
        char_x = active_char.char_base.char_pos_x
        char_y = active_char.char_base.char_pos_y
        
        if char_x is None or char_y is None:
            print("\n[NEXT >>] Не удалось прочитать координаты")
            return
        
        # Проверяем все точки
        for point in DUNGEON_POINTS:
            trigger_x, trigger_y = point['trigger']  # 2 координаты!
            target_x, target_y, target_z = point['target']  # 3 координаты!
            radius = point.get('radius', 15.0)  # используем 'radius' вместо 'trigger_radius'
            count_in_limits = point.get('count_in_limits', True)
            
            # Дистанция до триггера (только X и Y)
            dx = abs(char_x - trigger_x)
            dy = abs(char_y - trigger_y)
            
            if dx <= radius and dy <= radius:
                # НАШЛИ ТРИГГЕР-ЗОНУ!
                print(f"\n[NEXT >>] В триггер-зоне точки: {point['name']}")
                
                # СОХРАНЯЕМ ТОЧКУ ДЛЯ REDO
                multibox_manager.last_teleport_destination = (target_x, target_y, target_z)
                
                # Проверяем наличие пати у активного персонажа
                from game.offsets import resolve_offset, OFFSETS
                party_ptr = resolve_offset(
                    active_char.memory,
                    OFFSETS["party_ptr"],
                    active_char.char_base.cache
                )
                
                has_party = (party_ptr and party_ptr != 0)
                
                if not has_party:
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
                        if count_in_limits:
                            action_limiter.record_usage('tp_next')
                    else:
                        print(f"\n[NEXT >>] {point['name']}: ошибка телепортации\n")
                else:
                    # ЕСТЬ ПАТИ - групповой телепорт
                    _, group = multibox_manager.get_leader_and_group()
                    
                    if group:
                        success_count = multibox_manager.teleport_group(
                            group,
                            target_x,
                            target_y,
                            target_z,
                            send_space=True
                        )
                        
                        if success_count > 0:
                            print(f"\n[NEXT >>] {point['name']}: телепортировано {success_count} персонажей\n")
                            if count_in_limits:
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
        """Телепортировать к точке LONG LEFT (НЕ расходует лимиты)"""
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
        """Телепортировать к точке LONG RIGHT (НЕ расходует лимиты)"""
        _tp_to_special_point("LONG RIGHT", LONG_RIGHT_POINT, "solo", multibox_manager, app_state)

    action_manager.register(
        'tp_long_right',
        label='LONG ->  [PRO]',
        type='quick',
        callback=action_long_right,
        has_hotkey=True,
        required_permission=PERMISSION_PRO
    )
    
    # === REDO >> (ВМЕСТО EXIT) ===
    def action_redo():
        """Телепортировать на последнюю сохраненную точку из NEXT"""
        if not multibox_manager.last_teleport_destination:
            print("\n[REDO >>] Нет сохраненной точки для REDO телепорта\n")
            return
        
        target_x, target_y, target_z = multibox_manager.last_teleport_destination
        
        # Берем активного персонажа
        active_char = app_state.last_active_character
        
        if not active_char:
            print("\n[REDO >>] Нет активного окна\n")
            return
        
        # Проверяем есть ли у него пати
        active_char.char_base.refresh()
        
        from game.offsets import resolve_offset, OFFSETS
        party_ptr = resolve_offset(
            active_char.memory,
            OFFSETS["party_ptr"],
            active_char.char_base.cache
        )
        
        has_party = (party_ptr and party_ptr != 0)
        
        if not has_party:
            # ОДИНОЧНЫЙ ТЕЛЕПОРТ
            success = multibox_manager.teleport_character(
                active_char,
                target_x,
                target_y,
                target_z,
                send_space=True
            )
            
            if success:
                print(f"\n[REDO >>] Телепортирован {active_char.char_base.char_name}\n")
            else:
                print(f"\n[REDO >>] Ошибка телепортации\n")
        else:
            # ГРУППОВОЙ ТЕЛЕПОРТ
            _, group = multibox_manager.get_leader_and_group()
            
            if group:
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

    # НЕ ЗАПИСЫВАЕМ action_limiter.record_usage() для REDO!

    action_manager.register(
        'tp_redo',
        label='REDO >>  [PRO]',
        type='quick',
        callback=action_redo,
        has_hotkey=True,
        required_permission=PERMISSION_PRO
    )


def _tp_to_special_point(point_name, point_data, mode, multibox_manager, app_state):
    """
    Универсальная функция телепорта к специальной точке
    
    Args:
        point_name: название точки (для логов)
        point_data: (x, y, z)
        mode: "solo" или "party"
        multibox_manager: менеджер мультибокса
        app_state: состояние приложения
    """
    target_x, target_y, target_z = point_data
    
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