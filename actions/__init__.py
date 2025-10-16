"""
Actions - модуль действий приложения
ОБНОВЛЕНО: убран headhunter_loop_callback (теперь в AHK)
"""
from actions.toggle_actions import (
    register_toggle_actions, 
    follow_loop_callback, 
    attack_loop_callback
)
from actions.try_actions import register_try_actions
from actions.pro_actions import register_pro_actions
from actions.dev_actions import register_dev_actions

__all__ = [
    'register_toggle_actions',
    'register_try_actions',
    'register_pro_actions',
    'register_dev_actions',
    'follow_loop_callback',
    'attack_loop_callback',
]