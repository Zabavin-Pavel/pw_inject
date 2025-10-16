import logging
from core.keygen import PERMISSION_TRY, PERMISSION_PRO, PERMISSION_DEV

def register_toggle_actions(action_manager, multibox_manager, ahk_manager, app_state, main_window):
    """
    Зарегистрировать все toggle действия
    
    Args:
        action_manager: менеджер действий
        multibox_manager: менеджер мультибокса
        ahk_manager: менеджер AHK
        app_state: состояние приложения
        main_window: главное окно (для запуска loops)
    """
    
    # === FOLLOW (TRY) - ИСПРАВЛЕНО ===
    def toggle_follow():
        """Toggle: Follow"""
        is_active = app_state.is_action_active('follow')
        
        if is_active:
            print("Follow: STARTED")
            main_window._start_action_loop('follow', lambda: follow_loop_callback(ahk_manager))
        else:
            print("Follow: STOPPED")
            main_window._stop_action_loop('follow')
    
    action_manager.register(
        'follow',
        label='Follow',
        type='toggle',
        callback=toggle_follow,
        icon='👣',
        has_hotkey=False,
        required_permission=PERMISSION_TRY
    )
    
    # === ATTACK (PRO) - ИСПРАВЛЕНО ===
    def toggle_attack():
        """Toggle: Атака (копирование таргета лидера)"""
        is_active = app_state.is_action_active('attack')
        
        if is_active:
            print("Attack: STARTED")
            # ИСПРАВЛЕНО: запускаем таймер
            main_window._start_action_loop('attack', lambda: attack_loop_callback(multibox_manager))
        else:
            print("Attack: STOPPED")
            # ИСПРАВЛЕНО: останавливаем таймер
            main_window._stop_action_loop('attack')
    
    action_manager.register(
        'attack',
        label='Attack',
        type='toggle',
        callback=toggle_attack,
        icon='⚔️',
        has_hotkey=False,
        required_permission=PERMISSION_PRO
    )
    
    # === HEADHUNTER (DEV) - ИСПРАВЛЕНО: фиксируем PID ===
    def toggle_headhunter():
        """Toggle: Headhunter (Tab + ЛКМ по 100, 100 для активного окна)"""
        is_active = app_state.is_action_active('headhunter')
        
        if is_active:
            print("Headhunter: STARTED")
            main_window._start_action_loop('headhunter', lambda: headhunter_loop_callback(ahk_manager))
        else:
            print("Headhunter: STOPPED")
            main_window._stop_action_loop('headhunter')

    action_manager.register(
        'headhunter',
        label='Headhunter',
        type='toggle',
        callback=toggle_headhunter,
        icon='☠',
        has_hotkey=False,
        required_permission=PERMISSION_DEV
    )

def follow_loop_callback(multibox_manager):
    """Callback для Follow loop (вызывается каждые 500ms)"""
    # print("🔍 follow_loop_callback CALLED")
    active_corrections = multibox_manager.follow_leader()
    # print(f"🔍 follow_loop_callback DONE, corrections={active_corrections}")

def attack_loop_callback(multibox_manager):
    """
    Callback для Attack loop (вызывается каждые 500ms)
    """
    try:
        success_count = multibox_manager.set_attack_target()
        if success_count > 0:
            logging.debug(f"Attack: {success_count} targets set")
    except Exception as e:
        logging.error(f"Error in attack_loop_callback: {e}")

def headhunter_loop_callback(ahk_manager):
    """Callback для Headhunter loop (вызывается каждые 200ms)"""
    try:
        ahk_manager.headhunter()
    except Exception as e:
        logging.error(f"Error in headhunter_loop_callback: {e}")

def follow_loop_callback(ahk_manager):
    """Callback для Follow loop (вызывается каждые 500ms)"""
    try:
        ahk_manager.follow()
    except Exception as e:
        logging.error(f"Error in follow_loop_callback: {e}")