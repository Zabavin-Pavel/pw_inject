"""
TRY уровень - базовые действия - ИСПРАВЛЕНО
"""
from core.keygen import PERMISSION_TRY
import logging


def register_try_actions(action_manager, ahk_manager, app_state, multibox_manager):
    """
    Зарегистрировать действия уровня TRY
    
    Args:
        action_manager: менеджер действий
        ahk_manager: менеджер AHK
        app_state: состояние приложения
        multibox_manager: менеджер мультибокса (для группы)
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

    # === follow_leader ===
    def ahk_follow_leader():
        """ПКМ + Ассист + ПКМ + Follow для членов группы (БЕЗ лидера)"""
        logging.info("🎯 ahk_follow_leader called")
        
        # Получаем лидера и группу
        leader, group = multibox_manager.get_leader_and_group()
        
        logging.info(f"   Leader: {leader.char_base.char_name if leader else None}")
        logging.info(f"   Group size: {len(group) if group else 0}")
        
        if not leader or not group:
            logging.warning("⚠️ No leader or group!")
            return
        
        # Вычисляем target PIDs (члены группы БЕЗ лидера)
        target_pids = []
        for member in group:
            logging.info(f"   Member: {member.char_base.char_name} (PID={member.pid})")
            if member.pid != leader.pid:  # Пропускаем лидера
                target_pids.append(member.pid)
        
        logging.info(f"   Target PIDs (without leader): {target_pids}")
        
        if target_pids:
            ahk_manager.follow_leader(target_pids=target_pids)
        else:
            logging.warning("⚠️ No target PIDs after filtering!")
    
    action_manager.register(
        'ahk_follow_leader',
        label='FOLLOW   [TRY]',
        type='quick',
        callback=ahk_follow_leader,
        has_hotkey=True,
        required_permission=PERMISSION_TRY
    )