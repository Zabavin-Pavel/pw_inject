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
        """Toggle: Следование"""
        is_active = app_state.is_action_active('follow')
        
        if is_active:
            print("Follow: STARTED")
            multibox_manager.start_follow_freeze()
            main_window._start_action_loop('follow', lambda: follow_loop_callback(multibox_manager))
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
        active_char = app_state.last_active_character
        
        # ОТЛАДКА
        print(f"\n=== toggle_headhunter CALLED ===")
        print(f"  is_active: {is_active}")
        print(f"  active_char: {active_char.char_base.char_name if active_char else None}")
        print(f"  active_char.pid: {active_char.pid if active_char else None}")
        
        if is_active:
            if not active_char:
                print("Headhunter: No active character")
                app_state.toggle_action('headhunter')  # Выключаем обратно
                return
            
            # КРИТИЧНО: Сохраняем PID при старте
            fixed_pid = active_char.pid
            
            print(f"Headhunter: STARTED for {active_char.char_base.char_name}")
            print(f"  Fixed PID: {fixed_pid}")
            
            # ИСПРАВЛЕНО: передаем зафиксированный PID в callback
            main_window._start_action_loop('headhunter', lambda: headhunter_loop_callback(ahk_manager, fixed_pid))
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

def headhunter_loop_callback(ahk_manager, fixed_pid):
    """
    Callback для Headhunter loop (вызывается каждые 200ms)
    
    Args:
        ahk_manager: менеджер AHK
        fixed_pid: зафиксированный PID окна (не меняется во время работы)
    """
    try:
        # ОТЛАДКА: только первые 3 раза
        if not hasattr(headhunter_loop_callback, 'call_count'):
            headhunter_loop_callback.call_count = 0
        
        headhunter_loop_callback.call_count += 1
        if headhunter_loop_callback.call_count <= 3:
            print(f"  headhunter_loop #{headhunter_loop_callback.call_count}: Calling AHK with FIXED PID={fixed_pid}")
        
        # Вызываем AHK функцию headhunter с ЗАФИКСИРОВАННЫМ PID
        result = ahk_manager.headhunter(fixed_pid)
        
        if headhunter_loop_callback.call_count <= 3:
            print(f"  headhunter_loop #{headhunter_loop_callback.call_count}: AHK result={result}")
        
    except Exception as e:
        logging.error(f"Error in headhunter_loop_callback: {e}")
        print(f"❌ Error in headhunter_loop: {e}")
        
    except Exception as e:
        logging.error(f"Error in headhunter_loop_callback: {e}")
        print(f"❌ Error in headhunter_loop: {e}")