"""
Генератор лицензий с уровнями доступа
"""
import hmac
import hashlib
import requests
from datetime import datetime, timedelta

TICKET_MAC = "TICKET"
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
            return dt.strftime('%d%m%y')
        else:
            return datetime.now().strftime('%d%m%y')
    except:
        return datetime.now().strftime('%d%m%y')

def parse_date(date_str: str) -> datetime:
    """Парсить дату из формата DDMMYY в datetime"""
    return datetime.strptime(date_str, '%d%m%y')

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

def generate_ticket(days_valid: int = 0, permission: str = PERMISSION_PRO) -> str:
    """
    Сгенерировать талон до конца дня (не привязан к MAC, работает для всех)
    
    Args:
        days_valid: Сколько дней действителен (0 = до конца сегодня, 1 = до конца завтра)
        permission: Уровень доступа
    
    Returns:
        Лицензионный ключ-талон (универсальный для всех)
    """
    target_date = datetime.now() + timedelta(days=days_valid)
    expiry = (target_date + timedelta(days=1)).strftime('%d%m%y')
    
    # Используем специальный TICKET_MAC вместо реального MAC
    return generate_license(TICKET_MAC, expiry, permission)

def verify_license(license_key: str, current_mac: str) -> tuple[bool, str, str]:
    """Проверить лицензионный ключ или талон"""
    try:
        parts = license_key.split('-')
        
        if len(parts) != 3:
            return False, PERMISSION_NONE, "Invalid license format"
        
        permission, expiry, signature = parts
        permission = permission.lower()
        
        if permission not in [PERMISSION_TRY, PERMISSION_PRO, PERMISSION_DEV]:
            return False, PERMISSION_NONE, f"Invalid permission: {permission}"
        
        # Сначала проверяем как обычную лицензию (с текущим MAC)
        data = f'{current_mac}-{expiry}-{permission}'
        expected_signature = hmac.new(
            SECRET_KEY, 
            data.encode(), 
            hashlib.sha256
        ).hexdigest()[:15]
        
        is_valid = (signature == expected_signature)
        
        # Если не подошло, проверяем как талон (с TICKET_MAC)
        if not is_valid:
            ticket_data = f'{TICKET_MAC}-{expiry}-{permission}'
            ticket_signature = hmac.new(
                SECRET_KEY,
                ticket_data.encode(),
                hashlib.sha256
            ).hexdigest()[:15]
            
            if signature != ticket_signature:
                return False, PERMISSION_NONE, "Invalid signature"
        
        # Проверка срока действия
        current_date_str = get_current_date()
        current_date = parse_date(current_date_str)
        expiry_date = parse_date(expiry)
        
        # ИСПРАВЛЕНО: используем <= вместо 
        if current_date >= expiry_date:
            return False, PERMISSION_NONE, f"License expired"
        
        return True, permission, "OK"
    
    except Exception as e:
        return False, PERMISSION_NONE, f"Verification error: {str(e)}"

# Тест
if __name__ == '__main__':
    USERS = {
        '1 Pawka': '238300919419878',
        '2 Sawka': '207794402335169',
        # '3 Evgen': '238300914231286',
        # '4 Wladik': '185410943814810',
        '5 Valek': '5025756573854',
        '6 Sergey': '27214211329154',
        # '7 Ruzlan': '198112242178987',
        '7 Roman': '18691165716581',
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
    
    print("=== Тест талонов ===\n")
    mac = '23855555555878'
    # Просроченный талон (вчера)
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%d%m%y')
    expired_key = generate_license(mac, yesterday, PERMISSION_PRO)
    print(f"Просроченный ключ (вчера {yesterday}): {expired_key}")
    success, perm, msg = verify_license(expired_key, mac)
    print(f"Результат: {success}, Уровень: {perm}, Сообщение: {msg}\n")
    
    # Талон на сегодня (до конца дня)
    today_ticket = generate_ticket(0, PERMISSION_PRO)
    print(f"Талон на сегодня:   {today_ticket}")
    today_ticket = generate_ticket(0, PERMISSION_TRY)
    print(f"Талон на сегодня:   {today_ticket}")
    # Проверяем с разными MAC
    # for test_mac in ['238300919419878', '84585009692719', '999999999999']:
    #     success, perm, msg = verify_license(today_ticket, test_mac)
    #     print(f"  MAC {test_mac}: {success}")
    
    # Талон на вчера
    delta_ticket = generate_ticket(-1, PERMISSION_PRO)
    print(f"\nТалон на вчера:   {delta_ticket}")
    # Проверяем с разными MAC
    # for test_mac in ['238300919419878', '84585009692719', '999999999999']:
    #     success, perm, msg = verify_license(delta_ticket, test_mac)
    #     print(f"  MAC {test_mac}: {success}")