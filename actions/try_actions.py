"""
TRY уровень - базовые действия - ИСПРАВЛЕНО
"""
from core.keygen import PERMISSION_TRY


def register_try_actions(action_manager, ahk_manager, app_state, multibox_manager):
    """
    Зарегистрировать действия уровня TRY
    
    Args:
        action_manager: менеджер действий
        ahk_manager: менеджер AHK
        app_state: состояние приложения
        multibox_manager: менеджер мультибокса (для excluded_pids)
    """
    
    # === LBM ===
    def ahk_click_mouse():
        """Клик ЛКМ в позиции курсора"""
        excluded_pids = list(multibox_manager.excluded_pids) if hasattr(multibox_manager, 'excluded_pids') else []
        ahk_manager.click_at_mouse(excluded_pids=excluded_pids)
    
    action_manager.register(
        'ahk_click_mouse',
        label='LBM      [TRY]',
        type='quick',
        callback=ahk_click_mouse,
        has_hotkey=True,
        required_permission=PERMISSION_TRY
    )

    # === follow_leader ===
    def ahk_follow_leader():
        """ПКМ + Ассист + ПКМ + Follow для членов группы (БЕЗ лидера)"""
        # Получаем все PIDs
        all_pids = set(multibox_manager.characters.keys()) if hasattr(multibox_manager, 'characters') else set()
        
        # Получаем excluded PIDs (лидер + не в группе)
        excluded = multibox_manager.excluded_pids if hasattr(multibox_manager, 'excluded_pids') else set()
        
        # Вычисляем target PIDs (члены группы без лидера)
        target_pids = list(all_pids - excluded)
        
        if target_pids:
            ahk_manager.follow_leader(target_pids=target_pids)
    
    action_manager.register(
        'ahk_follow_leader',
        label='FOLLOW   [TRY]',
        type='quick',
        callback=ahk_follow_leader,
        has_hotkey=True,
        required_permission=PERMISSION_TRY
    )