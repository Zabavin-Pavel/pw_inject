"""
TRY уровень - базовые действия - ИСПРАВЛЕНО
"""
from core.keygen import PERMISSION_TRY

def register_try_actions(action_manager, ahk_manager, app_state):
    """
    Зарегистрировать действия уровня TRY
    
    Args:
        action_manager: менеджер действий
        ahk_manager: менеджер AHK
        app_state: состояние приложения (для получения группы)
    """
    
    # === LBM ===
    def ahk_click_mouse():
        """Клик ЛКМ в позиции курсора"""
        ahk_manager.click_at_mouse()
    
    action_manager.register(
        'ahk_click_mouse',
        label='LBM      [TRY]',
        type='quick',
        callback=ahk_click_mouse,
        has_hotkey=True,
        required_permission=PERMISSION_TRY
    )

    # === SPACE ===
    def ahk_press_space():
        """Нажать Space на всех окнах"""
        ahk_manager.send_key("Space")
    
    action_manager.register(
        'ahk_press_space',
        label='SPACE    [TRY]',
        type='quick',
        callback=ahk_press_space,
        has_hotkey=True,
        required_permission=PERMISSION_TRY
    )

    # === FOLLOW_LIDER - ИСПРАВЛЕНО ===
    def ahk_follow_lider():
        """
        ЛКМ + ПКМ по 100,100 для членов группы (БЕЗ лидера)
        
        ИСПРАВЛЕНО:
        - Получает PIDs группы через app_state
        - Передает PIDs в AHK
        """
        # Получаем активного персонажа (лидера)
        leader = app_state.last_active_character
        
        if not leader:
            print("FOLLOW_LIDER: Нет активного окна")
            return
        
        # Получаем группу (всех кроме лидера)
        group_pids = []
        
        # Проходим по всем персонажам
        for pid, char_id in app_state.char_map.items():
            # Пропускаем лидера
            if pid == leader.pid:
                continue
            
            # Добавляем в список
            group_pids.append(pid)
        
        if not group_pids:
            print("FOLLOW_LIDER: Нет членов группы")
            return
        
        # ИСПРАВЛЕНО: передаем PIDs в AHK
        ahk_manager.follow_lider(group_pids)
        print(f"FOLLOW_LIDER: Отправлено {len(group_pids)} персонажам")
    
    action_manager.register(
        'ahk_follow_lider',
        label='FOLLOW   [TRY]',
        type='quick',
        callback=ahk_follow_lider,
        has_hotkey=True,
        required_permission=PERMISSION_TRY
    )