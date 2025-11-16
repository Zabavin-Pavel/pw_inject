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
        
        # НОВОЕ: Получаем реального лидера из памяти
        from game.offsets import resolve_offset, OFFSETS
        
        leader.char_base.refresh()
        party_ptr = resolve_offset(leader.memory, OFFSETS["party_ptr"], leader.char_base.cache)
        
        if not party_ptr or party_ptr == 0:
            logging.warning("⚠️ No party!")
            return
        
        party_leader_id = resolve_offset(leader.memory, OFFSETS["party_leader_id"], leader.char_base.cache)
        
        if not party_leader_id:
            logging.warning("⚠️ No party_leader_id!")
            return
        
        logging.info(f"   Party leader ID: {party_leader_id}")
        
        # Фильтруем: исключаем реального лидера + тех у кого нет группы
        target_pids = []
        real_leader_pid = None
        
        for member in group:
            member.char_base.refresh()
            
            # Проверяем есть ли у члена группа
            member_party_ptr = resolve_offset(member.memory, OFFSETS["party_ptr"], member.char_base.cache)
            
            if not member_party_ptr or member_party_ptr == 0:
                logging.info(f"   {member.char_base.char_name}: skipped (no party)")
                continue
            
            # Проверяем кто лидер
            if member.char_base.char_id == party_leader_id:
                real_leader_pid = member.pid
                logging.info(f"   {member.char_base.char_name}: REAL LEADER (excluded)")
            else:
                target_pids.append(member.pid)
                logging.info(f"   {member.char_base.char_name}: added to targets")
        
        logging.info(f"   Real leader PID: {real_leader_pid}")
        logging.info(f"   Target PIDs: {target_pids}")
        
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