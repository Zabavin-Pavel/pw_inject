"""
Менеджер лицензий
"""
import logging
from keygen import verify_license, get_mac_address

class LicenseManager:
    """Менеджер верификации лицензий"""
    
    @staticmethod
    def verify_from_settings(hwid: str, key: str) -> bool:
        """
        Проверить лицензию из settings
        
        Args:
            hwid: Сохранённый MAC адрес из settings
            key: Лицензионный ключ
        
        Returns:
            True если лицензия валидна
        """
        if not key or key == "":
            logging.warning("License verification failed: empty key")
            return False
        
        # Получаем текущий MAC
        current_mac = get_mac_address()
        
        # Проверяем лицензию
        success, message = verify_license(key, current_mac)
        
        if success:
            logging.info(f"License verification: SUCCESS")
            return True
        else:
            logging.warning(f"License verification: FAILED - {message}")
            return False