"""
Менеджер лицензий с поддержкой талонов и уровней доступа
Работает с license.ini
"""
import logging
from keygen import (
    verify_license, 
    get_mac_address, 
    compare_permissions,
    PERMISSION_NONE
)

class LicenseManager:
    """Менеджер верификации лицензий"""
    
    @staticmethod
    def verify_best_license(license_config) -> tuple[bool, str]:
        """
        Проверить талон и ключ, выбрать наивысший уровень доступа
        
        Логика:
        1. Перечитать license.ini (чтобы подхватить изменения)
        2. Проверить талон (если есть)
        3. Проверить основной ключ (если есть)
        4. Выбрать наивысший уровень доступа
        
        Args:
            license_config: объект LicenseConfig для чтения license.ini
        
        Returns:
            (success: bool, permission_level: str)
            - success: True если хотя бы один ключ валиден
            - permission_level: "none" / "try" / "pro" / "dev"
        """
        # НОВОЕ: Перечитываем файл перед проверкой
        license_config.reload()
        
        current_mac = get_mac_address()
        
        # Обновляем hwid в license.ini (только если изменился)
        if license_config.get_hwid() != current_mac:
            license_config.set_hwid(current_mac)
        
        # Читаем ключи из license.ini
        key = license_config.get_key()
        ticket = license_config.get_ticket()
        
        best_permission = PERMISSION_NONE
        has_valid_license = False
        
        # === ПРОВЕРКА ТАЛОНА (приоритет) ===
        if ticket and ticket != "":
            ticket_success, ticket_perm, ticket_msg = verify_license(ticket, current_mac)
            
            if ticket_success:
                logging.info(f"✅ Ticket valid: {ticket_perm}")
                best_permission = compare_permissions(best_permission, ticket_perm)
                has_valid_license = True
            else:
                logging.warning(f"❌ Ticket invalid: {ticket_msg}")
        
        # === ПРОВЕРКА ОСНОВНОГО КЛЮЧА ===
        if key and key != "":
            key_success, key_perm, key_msg = verify_license(key, current_mac)
            
            if key_success:
                logging.info(f"✅ Key valid: {key_perm}")
                best_permission = compare_permissions(best_permission, key_perm)
                has_valid_license = True
            else:
                logging.warning(f"❌ Key invalid: {key_msg}")
        
        # === ИТОГОВЫЙ РЕЗУЛЬТАТ ===
        if has_valid_license:
            logging.info(f"🎯 Best permission level: {best_permission}")
            return True, best_permission
        else:
            logging.warning("❌ No valid license found")
            return False, PERMISSION_NONE