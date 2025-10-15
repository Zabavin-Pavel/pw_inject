"""
Toggle действия (Follow, Attack, Headhunter) - ИСПРАВЛЕНО
"""
import logging
from core.keygen import PERMISSION_TRY, PERMISSION_PRO, PERMISSION_DEV

def register_toggle_actions(action_manager, multibox_manager, ahk_manager, app_state):
    """
    Зарегистрировать все toggle действия
    
    Args:
        action_manager: менеджер действий
        multibox_manager: менеджер мультибокса
        ahk_manager: менеджер AHK
        app_state: состояние приложения
    """
    
    # === FOLLOW (TRY) - ИСПРАВЛЕНО ===
    def toggle_follow():
        """
        Toggle: Следование (синхронизация полета)
        
        ИСПРАВЛЕНО:
        - Работает только для окон в пати с лидером
        - Проверяет локацию перед морозкой
        - Управление полетом через fly_trigger (когда найдены 2 состояния)
        """
        is_active = app_state.is_action_active('follow')
        
        if is_active:
            print("Follow: STARTED")
        else:
            print("Follow: STOPPED")
            
            # Разморозить всех при остановке
            for char in multibox_manager.get_all_characters():
                if char.fly_freeze_info and char.fly_freeze_info['active']:
                    char.memory.unfreeze_address(char.fly_freeze_info)
                    char.fly_freeze_info = None
                    char.char_base.set_fly_speed_z(0)
    
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
        """
        Toggle: Атака (копирование таргета лидера)
        
        ИСПРАВЛЕНО:
        - Использует новую логику get_leader_and_group
        - Правильно работает с оффсетами
        """
        is_active = app_state.is_action_active('attack')
        
        if is_active:
            print("Attack: STARTED")
        else:
            print("Attack: STOPPED")
    
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
        """
        Toggle: Headhunter (Tab + ЛКМ по 100, 100 для активного окна)
        
        ИСПРАВЛЕНО:
        - Запоминает активное окно при включении
        - Продолжает работать с этим окном даже после переключения
        """
        is_active = app_state.is_action_active('headhunter')
        
        active_char = app_state.last_active_character
        
        if is_active:
            if not active_char:
                print("Headhunter: No active character")
                app_state.toggle_action('headhunter')  # Выключаем обратно
                return
            
            print(f"Headhunter: STARTED for {active_char.char_base.char_name}")
        else:
            print("Headhunter: STOPPED")
    
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
    """
    Callback для Follow loop (вызывается каждые 500ms)
    
    ИСПРАВЛЕНО:
    - Использует новую логику из manager.follow_leader()
    - Проверяет локацию, управляет fly_trigger
    """
    active_corrections = multibox_manager.follow_leader()
    if active_corrections > 0:
        logging.debug(f"Follow: {active_corrections} active corrections")


def attack_loop_callback(multibox_manager):
    """
    Callback для Attack loop (вызывается каждые 500ms)
    
    ИСПРАВЛЕНО:
    - Использует новую логику из manager.set_attack_target()
    """
    success_count = multibox_manager.set_attack_target()
    if success_count > 0:
        logging.debug(f"Attack: {success_count} targets set")


def headhunter_loop_callback(ahk_manager, app_state):
    """
    Callback для Headhunter loop (вызывается каждые 200ms)
    
    ИСПРАВЛЕНО:
    - Работает с последним активным окном
    - Продолжает даже после переключения на другое окно
    """
    active_char = app_state.last_active_character
    
    if not active_char:
        return
    
    # Вызываем AHK функцию headhunter с PID
    ahk_manager.headhunter(active_char.pid)