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
    required_permission: str = "try"  # НОВОЕ: Требуемый уровень доступа

class ActionManager:
    """Менеджер действий"""
    
    def __init__(self, app_state):
        self.app_state = app_state
        self.actions = {}  # {action_id: Action}
    
    def register(self, action_id: str, label: str, type: str, callback: Callable, 
                 icon: str = None, has_hotkey: bool = True, required_permission: str = "try"):
        """
        Зарегистрировать действие
        
        Args:
            action_id: Уникальный ID
            label: Название для UI
            type: 'quick' (клик = выполнение) или 'toggle' (клик = вкл/выкл)
            callback: Функция для выполнения
            icon: Иконка (если None - только хоткей)
            has_hotkey: Есть ли поле для хоткея
            required_permission: НОВОЕ: Требуемый уровень доступа ("try", "pro", "dev")
        """
        action = Action(
            id=action_id,
            label=label,
            type=type,
            callback=callback,
            icon=icon,
            has_hotkey=has_hotkey,
            required_permission=required_permission
        )
        
        self.actions[action_id] = action
    
    def execute(self, action_id: str):
        """Выполнить действие (с проверкой доступа)"""
        if action_id not in self.actions:
            logging.error(f"Action not found: {action_id}")
            return
        
        action = self.actions[action_id]
        
        # НОВОЕ: Проверка прав доступа
        if not self.app_state.has_permission(action.required_permission):
            logging.warning(f"Access denied to action '{action_id}': requires {action.required_permission}, current: {self.app_state.permission_level}")
            return
        
        try:
            action.callback()
        except Exception as e:
            logging.error(f"Error executing action {action_id}: {e}")
    
    def get_icon_actions(self):
        """Получить действия с иконками (без хоткеев) - ТОЛЬКО ДОСТУПНЫЕ"""
        return [a for a in self.actions.values() 
                if a.icon and not a.has_hotkey 
                and self.app_state.has_permission(a.required_permission)]
    
    def get_hotkey_actions(self):
        """Получить действия с хоткеями (без иконок) - ТОЛЬКО ДОСТУПНЫЕ"""
        return [a for a in self.actions.values() 
                if a.has_hotkey and not a.icon 
                and self.app_state.has_permission(a.required_permission)]
    
    def get_action(self, action_id: str) -> Optional[Action]:
        """Получить действие по ID"""
        return self.actions.get(action_id)
    
    def is_action_accessible(self, action_id: str) -> bool:
        """НОВОЕ: Проверить доступно ли действие для текущего уровня"""
        action = self.actions.get(action_id)
        if not action:
            return False
        
        return self.app_state.has_permission(action.required_permission)