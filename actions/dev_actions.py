"""
DEV уровень - продвинутые действия для разработки
"""
from core.keygen import PERMISSION_DEV
from config.constants import SO_POINT, GO_POINT

def register_dev_actions(action_manager, multibox_manager, app_state):
    """
    Зарегистрировать действия уровня DEV
    
    Args:
        action_manager: менеджер действий
        multibox_manager: менеджер мультибокса
        app_state: состояние приложения
    """
    
    # === РАЗДЕЛИТЕЛЬ ===
    action_manager.register(
        'separator_dev',
        label='',  # Пустая строка - визуал через SeparatorRow
        type='quick',
        callback=lambda: None,
        has_hotkey=True,  # Чтобы попал в get_hotkey_actions()
        required_permission=PERMISSION_DEV,
        is_separator=True  # НОВОЕ - это разделитель
    )
    
    # === ACT SO ===
    def action_tp_to_so():
        """TP to SO (только последнее активное окно, С ОДИНОЧНЫМ SPACE)"""
        active_char = app_state.last_active_character
        
        if not active_char:
            print("\n[ACT SO] Нет активного окна")
            return
        
        target_x, target_y, target_z = SO_POINT
        
        success = multibox_manager.teleport_character(
            active_char,
            target_x,
            target_y,
            target_z,
            send_space=True
        )
        
        if success:
            print(f"\n[ACT SO] Телепортирован {active_char.char_base.char_name}\n")
        else:
            print("\n[ACT SO] Ошибка телепортации\n")
    
    action_manager.register(
        'tp_to_so',
        label='QB SO    [DEV]',
        type='quick',
        callback=action_tp_to_so,
        has_hotkey=True,
        required_permission=PERMISSION_DEV
    )
    
    # === ACT GO ===
    def action_tp_to_go():
        """TP to GO (только последнее активное окно, С ОДИНОЧНЫМ SPACE)"""
        active_char = app_state.last_active_character
        
        if not active_char:
            print("\n[ACT GO] Нет активного окна")
            return
        
        target_x, target_y, target_z = GO_POINT
        
        success = multibox_manager.teleport_character(
            active_char,
            target_x,
            target_y,
            target_z,
            send_space=True
        )
        
        if success:
            print(f"\n[ACT GO] Телепортирован {active_char.char_base.char_name}\n")
        else:
            print("\n[ACT GO] Ошибка телепортации\n")
    
    action_manager.register(
        'tp_to_go',
        label='QB GO    [DEV]',
        type='quick',
        callback=action_tp_to_go,
        has_hotkey=True,
        required_permission=PERMISSION_DEV
    )