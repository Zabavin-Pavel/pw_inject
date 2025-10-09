"""
Генератор лицензий
"""
import hmac
import hashlib
import requests
from datetime import datetime

SECRET_KEY = b'XQC'

def get_current_year_month() -> str:
    """Получить текущий год-месяц из онлайн API"""
    try:
        response = requests.get('http://worldtimeapi.org/api/timezone/Etc/UTC', timeout=5)
        if response.status_code == 200:
            data = response.json()
            dt = datetime.fromisoformat(data['datetime'].replace('Z', '+00:00'))
            return dt.strftime('%Y%m')  # Формат: "202510"
        else:
            # Fallback на локальное время
            return datetime.now().strftime('%Y%m')
    except:
        # Fallback на локальное время
        return datetime.now().strftime('%Y%m')

def generate_license(mac_address: str, expiry_year_month: str) -> str:
    """
    Сгенерировать лицензионный ключ
    
    Args:
        mac_address: MAC адрес (например "238300919419878")
        expiry_year_month: Срок действия в формате YYYYMM (например "202508")
    
    Returns:
        Лицензионный ключ в формате "MAC-YYYYMM-SIGNATURE"
    """
    data = f'{mac_address}-{expiry_year_month}'
    signature = hmac.new(SECRET_KEY, data.encode(), hashlib.sha256).hexdigest()
    return f'{data}-{signature}'

def verify_license(license_key: str, current_mac: str) -> tuple[bool, str]:
    """
    Проверить лицензионный ключ
    
    Args:
        license_key: Лицензионный ключ
        current_mac: Текущий MAC адрес
    
    Returns:
        (success: bool, error_message: str)
    """
    try:
        parts = license_key.split('-')
        
        if len(parts) != 3:
            return False, "Invalid license format"
        
        mac, expiry, signature = parts
        
        # Проверка MAC адреса
        if mac != current_mac:
            return False, f"MAC mismatch (expected {mac}, got {current_mac})"
        
        # Проверка подписи
        expected_signature = hmac.new(
            SECRET_KEY, 
            f'{mac}-{expiry}'.encode(), 
            hashlib.sha256
        ).hexdigest()
        
        if signature != expected_signature:
            return False, "Invalid signature"
        
        # Проверка срока действия
        current_ym = get_current_year_month()
        
        if expiry < current_ym:
            return False, f"License expired ({expiry} < {current_ym})"
        
        return True, "OK"
    
    except Exception as e:
        return False, f"Verification error: {str(e)}"

def get_mac_address() -> str:
    """Получить MAC адрес (первый активный сетевой интерфейс)"""
    import uuid
    mac = uuid.getnode()
    return str(mac)

# Для генерации ключей (запускать вручную)
if __name__ == '__main__':
    USERS = {
        '1 Pawka': '238300919419878',
        '2 Sawka': '84585009692719',
        '3 Evgen': '238300914231286',
        '4 Wladik': '185410943814810',
        '5 Valek': '5025756573854',
        '6 Sergey': '27214211329154',
        '7 Ruzlan': '198112242178987',
    }
    EXPIRY = '202510'  # Срок действия: август 2025

    print("=== Мой адресс ===\n")
    print(get_mac_address())
    
    print("=== Лицензионные ключи ===\n")
    for user, mac_address in USERS.items():
        key = generate_license(mac_address, EXPIRY)
        print(f'{user}: {key}')
    
    print("\n=== Проверка первого ключа ===")
    test_key = generate_license('238300919419878', EXPIRY)
    success, msg = verify_license(test_key, '238300919419878')
    print(f"Результат: {success}, Сообщение: {msg}")