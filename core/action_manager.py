"""
Менеджер действий
"""
import logging
from dataclasses import dataclass
from typing import Callable, Optional

@dataclass
class Action:
    """Описание действия"""
    id: str                          # Уникальный ID
    label: str                       # Название для UI
    type: str                        # 'quick' или 'toggle'
    callback: Callable               # Функция для выполнения
    icon: Optional[str] = None       # Иконка (если есть)
    has_hotkey: bool = True          # Есть ли поле хоткея

class ActionManager:
    """Менеджер действий"""
    
    def __init__(self, app_state):
        self.app_state = app_state
        self.actions = {}  # {action_id: Action}
    
    def register(self, action_id: str, label: str, type: str, callback: Callable, 
                 icon: str = None, has_hotkey: bool = True):
        """
        Зарегистрировать действие
        
        Args:
            action_id: Уникальный ID
            label: Название для UI
            type: 'quick' (клик = выполнение) или 'toggle' (клик = вкл/выкл)
            callback: Функция для выполнения
            icon: Иконка (если None - только хоткей)
            has_hotkey: Есть ли поле для хоткея
        """
        action = Action(
            id=action_id,
            label=label,
            type=type,
            callback=callback,
            icon=icon,
            has_hotkey=has_hotkey
        )
        
        self.actions[action_id] = action
    
    def execute(self, action_id: str):
        """Выполнить действие"""
        if action_id not in self.actions:
            logging.error(f"Action not found: {action_id}")
            return
        
        action = self.actions[action_id]
        
        try:
            action.callback()
        except Exception as e:
            logging.error(f"Error executing action {action_id}: {e}")
    
    def get_icon_actions(self):
        """Получить действия с иконками (без хоткеев)"""
        return [a for a in self.actions.values() if a.icon and not a.has_hotkey]
    
    def get_hotkey_actions(self):
        """Получить действия с хоткеями (без иконок)"""
        return [a for a in self.actions.values() if a.has_hotkey and not a.icon]
    
    def get_action(self, action_id: str) -> Optional[Action]:
        """Получить действие по ID"""
        return self.actions.get(action_id)