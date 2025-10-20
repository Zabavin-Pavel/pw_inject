"""
DEV уровень - продвинутые действия для разработки
"""
from core.keygen import PERMISSION_DEV
# from config.constants import SO_POINT, GO_POINT

def register_dev_actions(action_manager, multibox_manager, app_state, action_limiter):
    """
    Зарегистрировать действия уровня DEV
    
    Args:
        action_manager: менеджер действий
        multibox_manager: менеджер мультибокса
        app_state: состояние приложения
        action_limiter: система лимитов
    """
    
    # # === РАЗДЕЛИТЕЛЬ ===
    # action_manager.register(
    #     'separator_dev',
    #     label='',
    #     type='quick',
    #     callback=lambda: None,
    #     has_hotkey=True,
    #     required_permission=PERMISSION_DEV,
    #     is_separator=True
    # )
    
    # # === QB SO ===
    # def action_tp_to_so():
    #     """TP to SO (только последнее активное окно, С ОДИНОЧНЫМ SPACE)"""
    #     # ПРОВЕРКА ЛИМИТА
    #     if not action_limiter.can_use('tp_to_so'):
    #         print("\n[QB SO] ⛔ Лимит использований достигнут")
    #         return
        
    #     active_char = app_state.last_active_character
        
    #     if not active_char:
    #         print("\n[QB SO] Нет активного окна")
    #         return
        
    #     target_x, target_y, target_z = SO_POINT
        
    #     active_char.char_base.refresh()
        
    #     success = multibox_manager.teleport_character(
    #         active_char,
    #         target_x,
    #         target_y,
    #         target_z,
    #         send_space=True
    #     )
        
    #     if success:
    #         print(f"\n[QB SO] Телепортирован {active_char.char_base.char_name}\n")
    #         # Записываем использование
    #         action_limiter.record_usage('tp_to_so')
    #     else:
    #         print("\n[QB SO] Ошибка телепортации\n")
    
    # action_manager.register(
    #     'tp_to_so',
    #     label='QB SO    [DEV]',
    #     type='quick',
    #     callback=action_tp_to_so,
    #     has_hotkey=True,
    #     required_permission=PERMISSION_DEV
    # )
    
    # # === QB GO ===
    # def action_tp_to_go():
    #     """TP to GO (только последнее активное окно, С ОДИНОЧНЫМ SPACE)"""
    #     # ПРОВЕРКА ЛИМИТА
    #     if not action_limiter.can_use('tp_to_go'):
    #         print("\n[QB GO] ⛔ Лимит использований достигнут")
    #         return
        
    #     active_char = app_state.last_active_character
        
    #     if not active_char:
    #         print("\n[QB GO] Нет активного окна")
    #         return
        
    #     target_x, target_y, target_z = GO_POINT
        
    #     active_char.char_base.refresh()
        
    #     success = multibox_manager.teleport_character(
    #         active_char,
    #         target_x,
    #         target_y,
    #         target_z,
    #         send_space=True
    #     )
        
    #     if success:
    #         print(f"\n[QB GO] Телепортирован {active_char.char_base.char_name}\n")
    #         # Записываем использование
    #         action_limiter.record_usage('tp_to_go')
    #     else:
    #         print("\n[QB GO] Ошибка телепортации\n")
    
    # action_manager.register(
    #     'tp_to_go',
    #     label='QB GO    [DEV]',
    #     type='quick',
    #     callback=action_tp_to_go,
    #     has_hotkey=True,
    #     required_permission=PERMISSION_DEV
    # )