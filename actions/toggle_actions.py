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
        """Toggle: Следование (ТЕСТ ЗАМОРОЗКИ)"""
        is_active = app_state.is_action_active('follow')
        
        print(f"🔍 toggle_follow called, is_active={is_active}")
        
        if is_active:
            print("Follow: STARTED (ТЕСТ ЗАМОРОЗКИ)")
            print("🔍 Starting action loop...")
            # КРИТИЧНО: Запускаем loop через main_window!
            main_window._start_action_loop('follow', lambda: follow_loop_callback(multibox_manager))
            print("🔍 Action loop started!")
        else:
            print("Follow: STOPPED")
            print("🔍 Stopping action loop...")
            # КРИТИЧНО: Останавливаем loop через main_window!
            main_window._stop_action_loop('follow')
            print("🔍 Action loop stopped!")
            
            # Разморозить всех при остановке
            for char in multibox_manager.get_all_characters():
                # Размораживаем HP
                if hasattr(char, 'hp_freeze') and char.hp_freeze and char.hp_freeze['active']:
                    char.memory.unfreeze_address(char.hp_freeze)
                    char.hp_freeze = None
    
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
    
    # === HEADHUNTER (DEV) - ИСПРАВЛЕНО ===
    def toggle_headhunter():
        """Toggle: Headhunter (Tab + ЛКМ по 100, 100 для активного окна)"""
        is_active = app_state.is_action_active('headhunter')
        
        active_char = app_state.last_active_character
        
        if is_active:
            if not active_char:
                print("Headhunter: No active character")
                app_state.toggle_action('headhunter')  # Выключаем обратно
                return
            
            print(f"Headhunter: STARTED for {active_char.char_base.char_name}")
            # ИСПРАВЛЕНО: запускаем таймер
            main_window._start_action_loop('headhunter', lambda: headhunter_loop_callback(ahk_manager, app_state))
        else:
            print("Headhunter: STOPPED")
            # ИСПРАВЛЕНО: останавливаем таймер
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
    print("🔍 follow_loop_callback CALLED")
    active_corrections = multibox_manager.follow_leader()
    print(f"🔍 follow_loop_callback DONE, corrections={active_corrections}")

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


def headhunter_loop_callback(ahk_manager, app_state):
    """
    Callback для Headhunter loop (вызывается каждые 200ms)
    """
    try:
        active_char = app_state.last_active_character
        
        if not active_char:
            return
        
        # Вызываем AHK функцию headhunter с PID
        ahk_manager.headhunter(active_char.pid)
    except Exception as e:
        logging.error(f"Error in headhunter_loop_callback: {e}")