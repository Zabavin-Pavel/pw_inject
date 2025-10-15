"""
TRY уровень - базовые действия
"""
from core.keygen import PERMISSION_TRY

def register_try_actions(action_manager, ahk_manager):
    """
    Зарегистрировать действия уровня TRY
    
    Args:
        action_manager: менеджер действий
        ahk_manager: менеджер AHK
    """
    
    # === LBM ===
    action_manager.register(
        'ahk_click_mouse',
        label='LBM      [TRY]',
        type='quick',
        callback=ahk_manager.click_at_mouse,
        has_hotkey=True,
        required_permission=PERMISSION_TRY
    )

    # === SPACE ===
    action_manager.register(
        'ahk_press_space',
        label='SPACE    [TRY]',
        type='quick',
        callback=lambda: ahk_manager.send_key("Space"),
        has_hotkey=True,
        required_permission=PERMISSION_TRY
    )

    # === FOLLOW_LIDER ===
    action_manager.register(
        'ahk_follow_lider',
        label='FOLLOW   [TRY]',
        type='quick',
        callback=ahk_manager.follow_lider,
        has_hotkey=True,
        required_permission=PERMISSION_TRY
    )