"""
Ядро приложения
"""
from core.app_state import AppState
from core.action_manager import ActionManager, Action
from core.hotkey_manager import HotkeyManager
from core.license import LicenseManager

__all__ = [
    'AppState',
    'ActionManager',
    'Action',
    'HotkeyManager',
    'LicenseManager',
]