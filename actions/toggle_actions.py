"""
Toggle действия - ОБНОВЛЕНО: Headhunter через AHK
"""
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
    
    # === FOLLOW (TRY) ===
    def toggle_follow():
        """Toggle: Follow"""
        is_active = app_state.is_action_active('follow')
        
        if is_active:
            print("Follow: STARTED")
            multibox_manager.start_follow_freeze()
            main_window._start_action_loop('follow', lambda: follow_loop_callback(multibox_manager, ahk_manager))
        else:
            print("Follow: STOPPED")
            main_window._stop_action_loop('follow')
            multibox_manager.stop_follow_freeze()
    
    action_manager.register(
        'follow',
        label='Follow',
        type='toggle',
        callback=toggle_follow,
        icon='👣',
        has_hotkey=False,
        required_permission=PERMISSION_TRY
    )
    
    # === ATTACK (PRO) ===
    def toggle_attack():
        pass
    
    action_manager.register(
        'attack',
        label='Attack',
        type='toggle',
        callback=toggle_attack,
        icon='⚔️',
        has_hotkey=False,
        required_permission=PERMISSION_PRO
    )
    
    # === HEADHUNTER (DEV) ===
    def toggle_headhunter():
        pass

    action_manager.register(
        'headhunter',
        label='Headhunter',
        type='toggle',
        callback=toggle_headhunter,
        icon='☠',
        has_hotkey=False,
        required_permission=PERMISSION_PRO
    )


# === CALLBACK ФУНКЦИИ ДЛЯ LOOPS ===

def follow_loop_callback(multibox_manager, ahk_manager):
    """
    Callback для Follow loop (вызывается каждые 500ms)
    
    Контролирует высоту полета членов группы относительно лидера
    """
    try:
        multibox_manager.follow_leader()
    except Exception as e:
        logging.error(f"Error in follow_loop_callback: {e}")

def attack_loop_callback(multibox_manager, ahk_manager, app_state):
    """Callback для Attack loop (вызывается каждые 500ms)"""
    from config.constants import GUARD_ID, BOSS_IDS
    
    active_char = app_state.last_active_character
    
    if not active_char:
        return
    
    active_char.char_base.refresh()
    target_id = active_char.char_base.target_id
    
    if not target_id or target_id == 0:
        return
    
    if target_id == GUARD_ID:
        ahk_manager.attack_guard()
    elif target_id in BOSS_IDS:
        ahk_manager.attack_boss()