"""
Генератор лицензий с уровнями доступа
"""
import hmac
import hashlib
import requests
from datetime import datetime

SECRET_KEY = b'OWL'

# Уровни доступа
PERMISSION_NONE = "none"
PERMISSION_TRY = "try"
PERMISSION_PRO = "pro"
PERMISSION_DEV = "dev"

# Иерархия уровней (для сравнения)
PERMISSION_HIERARCHY = {
    PERMISSION_NONE: 0,
    PERMISSION_TRY: 1,
    PERMISSION_PRO: 2,
    PERMISSION_DEV: 3,
}

def get_current_date() -> str:
    """Получить текущую дату из онлайн API в формате DDMMYY"""
    try:
        response = requests.get('http://worldtimeapi.org/api/timezone/Etc/UTC', timeout=5)
        if response.status_code == 200:
            data = response.json()
            dt = datetime.fromisoformat(data['datetime'].replace('Z', '+00:00'))
            return dt.strftime('%d%m%y')  # Формат: "051025"
        else:
            return datetime.now().strftime('%d%m%y')
    except:
        return datetime.now().strftime('%d%m%y')

def generate_license(mac_address: str, expiry_date: str, permission: str = PERMISSION_TRY) -> str:
    """
    Сгенерировать лицензионный ключ
    
    Args:
        mac_address: MAC адрес (например "238300919419878")
        expiry_date: Срок действия в формате DDMMYY (например "051025" = 5 октября 2025)
        permission: Уровень доступа ("try", "pro", "dev")
    
    Returns:
        Лицензионный ключ в формате "PERMISSION-DDMMYY-SIGNATURE[:15]"
        Пример: "DEV-311025-15fc811bcc"
    """
    if permission not in [PERMISSION_TRY, PERMISSION_PRO, PERMISSION_DEV]:
        raise ValueError(f"Invalid permission: {permission}")
    
    # Генерируем signature на основе MAC-DDMMYY-PERMISSION
    data = f'{mac_address}-{expiry_date}-{permission}'
    signature = hmac.new(SECRET_KEY, data.encode(), hashlib.sha256).hexdigest()
    
    # Берём только первые 10 символов signature
    short_signature = signature[:15]
    
    # Формат: PERMISSION-DDMMYY-SIGNATURE (без MAC!)
    return f'{permission.upper()}-{expiry_date}-{short_signature}'

def verify_license(license_key: str, current_mac: str) -> tuple[bool, str, str]:
    """
    Проверить лицензионный ключ
    
    Args:
        license_key: Лицензионный ключ в формате "PERMISSION-DDMMYY-SIGNATURE"
        current_mac: Текущий MAC адрес
    
    Returns:
        (success: bool, permission_level: str, error_message: str)
    """
    try:
        parts = license_key.split('-')
        
        if len(parts) != 3:
            return False, PERMISSION_NONE, "Invalid license format (expected 3 parts)"
        
        permission, expiry, signature = parts
        
        # Нормализуем permission (из uppercase в lowercase)
        permission = permission.lower()
        
        # Проверка уровня доступа
        if permission not in [PERMISSION_TRY, PERMISSION_PRO, PERMISSION_DEV]:
            return False, PERMISSION_NONE, f"Invalid permission: {permission}"
        
        # Проверка подписи (генерируем на основе ТЕКУЩЕГО MAC!)
        data = f'{current_mac}-{expiry}-{permission}'
        expected_signature = hmac.new(
            SECRET_KEY, 
            data.encode(), 
            hashlib.sha256
        ).hexdigest()[:15]  # Берём первые 15 символов
        
        if signature != expected_signature:
            return False, PERMISSION_NONE, f"Invalid signature (expected {expected_signature}, got {signature})"
        
        # Проверка срока действия
        current_date = get_current_date()
        
        if expiry < current_date:
            return False, PERMISSION_NONE, f"License expired ({expiry} < {current_date})"
        
        return True, permission, "OK"
    
    except Exception as e:
        return False, PERMISSION_NONE, f"Verification error: {str(e)}"

def compare_permissions(perm1: str, perm2: str) -> str:
    """
    Сравнить два уровня доступа и вернуть наивысший
    
    Args:
        perm1: первый уровень
        perm2: второй уровень
    
    Returns:
        Наивысший уровень доступа
    """
    level1 = PERMISSION_HIERARCHY.get(perm1, 0)
    level2 = PERMISSION_HIERARCHY.get(perm2, 0)
    
    return perm1 if level1 >= level2 else perm2

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
    EXPIRY = '311025'  # 31 октября 2025
    
    print("=== Мой MAC адрес ===\n")
    print(get_mac_address())
    print(f"\nТекущая дата: {get_current_date()}")
    
    print("\n=== Лицензионные ключи (TRY) ===\n")
    for user, mac_address in USERS.items():
        key = generate_license(mac_address, EXPIRY, PERMISSION_TRY)
        print(f'{user}: {key}')
    
    print("\n=== Лицензионные ключи (PRO) ===\n")
    for user, mac_address in USERS.items():
        key = generate_license(mac_address, EXPIRY, PERMISSION_PRO)
        print(f'{user}: {key}')
    
    print("\n=== Лицензионные ключи (DEV) ===\n")
    for user, mac_address in USERS.items():
        key = generate_license(mac_address, EXPIRY, PERMISSION_DEV)
        print(f'{user}: {key}')
    
    print("\n=== Талон на 1 день (PRO) ===")
    from datetime import timedelta
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%d%m%y')
    ticket = generate_license('238300919419878', tomorrow, PERMISSION_PRO)
    print(f'Ticket (expires {tomorrow}): {ticket}')
    
    print("\n=== Проверка ключа ===")
    test_key = generate_license('238300919419878', EXPIRY, PERMISSION_PRO)
    print(f"Generated key: {test_key}")
    success, perm, msg = verify_license(test_key, '238300919419878')
    print(f"Результат: {success}, Уровень: {perm}, Сообщение: {msg}")