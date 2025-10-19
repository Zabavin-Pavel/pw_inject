"""
Система лимитов использования экшенов с двойными логами и защитой от читеров
"""
import hashlib
import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Часовой пояс МСК (UTC+3)
MSK = timezone(timedelta(hours=3))

class ActionLimiter:
    """Управление лимитами использования экшенов с защитой от читеров"""
    
    # Лимиты по группам экшенов
    LIMITS = {
        'tp': 200,  # NEXT/LONG (общий счетчик)
        'qb': 100,  # QBSO/QBGO (общий счетчик)
    }
    
    # Маппинг экшенов на группы
    ACTION_GROUPS = {
        'tp_next': 'tp',
        'tp_long_left': 'tp',
        'tp_long_right': 'tp',
        'tp_exit': 'tp',
        'tp_to_so': 'qb',
        'tp_to_go': 'qb',
    }
    
    def __init__(self):
        """Инициализация с двумя файлами логов"""
        # ОСНОВНЫЕ ЛОГИ (защищенные) в Discord
        discord_dir = Path.home() / "AppData" / "Local" / "Discord"
        discord_dir.mkdir(parents=True, exist_ok=True)
        self.main_log_file = discord_dir / "app.log"
        
        # ПРИМАНКА (для отвода глаз) в xvocmuk
        decoy_dir = Path.home() / "AppData" / "Local" / "xvocmuk"
        decoy_dir.mkdir(parents=True, exist_ok=True)
        self.decoy_log_file = decoy_dir / "action_usage.log"
        
        logging.info(f"📁 Main logs: {self.main_log_file}")
        logging.info(f"📁 Decoy logs: {self.decoy_log_file}")
        
        # Кеш текущих счетчиков (быстрая проверка)
        self.counters = {
            'tp': 0,
            'qb': 0,
        }
        
        # Кеш состояния лимитов (для быстрой проверки в начале экшена)
        self.limits_reached = {
            'tp': False,
            'qb': False,
        }
        
        # Флаг блокировки (если обнаружена попытка читерства)
        self.is_blocked = False
        self.block_reason = ""
        
        # Инициализация при старте
        self._load_counters_from_logs()
        self._check_decoy_integrity()
    
    def _get_msk_now(self):
        """Получить текущее время МСК"""
        return datetime.now(MSK)
    
    def _get_msk_date(self):
        """Получить текущую дату МСК (строка YYYY-MM-DD)"""
        return self._get_msk_now().strftime('%Y-%m-%d')
    
    def _compute_hash(self, data: str, prev_hash: str = "") -> str:
        """
        Вычислить хеш записи
        
        Args:
            data: данные записи (дата + action_group)
            prev_hash: хеш предыдущей записи (для цепочки)
        
        Returns:
            SHA256 хеш
        """
        combined = f"{prev_hash}:{data}"
        return hashlib.sha256(combined.encode()).hexdigest()
    
    def _read_logs(self, log_file: Path):
        """
        Прочитать и валидировать логи
        
        Args:
            log_file: путь к файлу логов
        
        Returns:
            list: список валидных записей [{date, action_group, hash}, ...]
        """
        if not log_file.exists():
            return []
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            records = []
            prev_hash = ""
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # ВАЖНО: Пропускаем служебные записи (блокировки, предупреждения)
                if line.startswith('### BLOCK ###') or line.startswith('### WARNING ###'):
                    continue
                
                try:
                    record = json.loads(line)
                    date = record.get('date')
                    action_group = record.get('action_group')
                    stored_hash = record.get('hash')
                    
                    if not all([date, action_group, stored_hash]):
                        logging.warning(f"Неполная запись в логах: {line}")
                        continue
                    
                    # Проверка хеша (защита от редактирования)
                    expected_hash = self._compute_hash(f"{date}:{action_group}", prev_hash)
                    
                    if expected_hash != stored_hash:
                        logging.error(f"❌ Лог поврежден! Хеш не совпадает: {line}")
                        # Все логи после этой записи считаем недействительными
                        break
                    
                    records.append(record)
                    prev_hash = stored_hash
                    
                except json.JSONDecodeError:
                    logging.warning(f"Невалидный JSON в логах: {line}")
                    continue
            
            return records
        
        except Exception as e:
            logging.error(f"Ошибка чтения логов {log_file}: {e}")
            return []
    
    def _check_decoy_integrity(self):
        """
        Проверить целостность приманки
        Если приманка изменена - установить блокировку до конца дня
        """
        # Читаем основные логи
        main_records = self._read_logs(self.main_log_file)
        
        # Читаем приманку
        decoy_records = self._read_logs(self.decoy_log_file)
        
        # Сравниваем количество записей
        if len(main_records) != len(decoy_records):
            self._trigger_soft_block("Decoy log count mismatch")
            return
        
        # Сравниваем содержимое
        for i, (main_rec, decoy_rec) in enumerate(zip(main_records, decoy_records)):
            if main_rec != decoy_rec:
                self._trigger_soft_block(f"Decoy log modified at line {i+1}")
                return
        
        # Если всё ок - разблокируем (на случай нового дня)
        if self.is_blocked:
            # Проверяем что блокировка не сегодняшняя
            if self._is_block_expired():
                self.is_blocked = False
                self.block_reason = ""
                logging.info("✅ Блокировка снята (новый день)")
    
    def _trigger_soft_block(self, reason: str):
        """
        Установить мягкую блокировку до конца дня
        
        Args:
            reason: причина блокировки
        """
        if self.is_blocked:
            return  # Уже заблокирован
        
        self.is_blocked = True
        self.block_reason = reason
        
        # Логируем в ОСНОВНЫЕ логи (Discord)
        block_record = {
            'timestamp': self._get_msk_now().isoformat(),
            'event': 'SOFT_BLOCK',
            'reason': reason,
            'date': self._get_msk_date()
        }
        
        try:
            with open(self.main_log_file, 'a', encoding='utf-8') as f:
                f.write(f"### BLOCK ### {json.dumps(block_record)}\n")
            
            logging.error(f"🚫 МЯГКАЯ БЛОКИРОВКА: {reason}")
            logging.error(f"🚫 Функции заблокированы до конца дня МСК")
            
        except Exception as e:
            logging.error(f"Ошибка записи блокировки: {e}")
    
    def _is_block_expired(self) -> bool:
        """Проверить истекла ли блокировка (новый день)"""
        # Читаем последнюю запись блокировки из основных логов
        if not self.main_log_file.exists():
            return True
        
        try:
            with open(self.main_log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Ищем последнюю блокировку
            for line in reversed(lines):
                if '### BLOCK ###' in line:
                    block_data = line.replace('### BLOCK ###', '').strip()
                    block_record = json.loads(block_data)
                    block_date = block_record.get('date')
                    
                    # Если блокировка сегодняшняя - еще активна
                    if block_date == self._get_msk_date():
                        return False
                    else:
                        return True
            
            return True  # Блокировок не найдено
            
        except Exception as e:
            logging.error(f"Ошибка проверки блокировки: {e}")
            return False
    
    def _load_counters_from_logs(self):
        """Загрузить счетчики из ОСНОВНЫХ логов при старте приложения"""
        records = self._read_logs(self.main_log_file)
        
        if not records:
            logging.info("📊 Логи использований пусты, счетчики обнулены")
            return
        
        today = self._get_msk_date()
        
        # Считаем использования за сегодня
        for record in records:
            if record['date'] == today:
                group = record['action_group']
                if group in self.counters:
                    self.counters[group] += 1
        
        # Обновляем кеш лимитов
        for group in self.counters:
            if self.counters[group] >= self.LIMITS[group]:
                self.limits_reached[group] = True
        
        logging.info(f"📊 Загружены счетчики: TP={self.counters['tp']}/{self.LIMITS['tp']}, QB={self.counters['qb']}/{self.LIMITS['qb']}")
    
    def _write_log_entry(self, action_group: str):
        """
        Записать использование экшена в ОБА лога (основной + приманка)
        
        Args:
            action_group: группа экшена ('tp' или 'qb')
        """
        # Читаем ОСНОВНЫЕ логи для получения хеша
        records = self._read_logs(self.main_log_file)
        
        # Берем хеш последней записи (или пустую строку для первой)
        prev_hash = records[-1]['hash'] if records else ""
        
        date = self._get_msk_date()
        data = f"{date}:{action_group}"
        new_hash = self._compute_hash(data, prev_hash)
        
        record = {
            'date': date,
            'action_group': action_group,
            'hash': new_hash
        }
        
        record_line = json.dumps(record) + '\n'
        
        # Пишем в ОСНОВНЫЕ логи (Discord)
        try:
            with open(self.main_log_file, 'a', encoding='utf-8') as f:
                f.write(record_line)
        except Exception as e:
            logging.error(f"Ошибка записи в основной лог: {e}")
        
        # Пишем в ПРИМАНКУ (xvocmuk)
        try:
            with open(self.decoy_log_file, 'a', encoding='utf-8') as f:
                f.write(record_line)
        except Exception as e:
            logging.error(f"Ошибка записи в приманку: {e}")
    
    def can_use(self, action_id: str) -> bool:
        """
        БЫСТРАЯ проверка: можно ли использовать экшен (из кеша)
        
        Args:
            action_id: ID экшена
        
        Returns:
            bool: True если можно использовать
        """
        # ПРОВЕРКА БЛОКИРОВКИ (ПРИОРИТЕТ #1)
        if self.is_blocked:
            # Проверяем истекла ли блокировка
            if not self._is_block_expired():
                logging.warning(f"🚫 Экшен заблокирован: {self.block_reason}")
                return False
            else:
                # Снимаем блокировку
                self.is_blocked = False
                self.block_reason = ""
                logging.info("✅ Блокировка снята (новый день)")
        
        # Периодическая проверка целостности приманки
        self._check_decoy_integrity()
        
        # Если блокировка установлена - отказ
        if self.is_blocked:
            return False
        
        # Проверяем переход на новый день МСК
        self._check_and_reset_if_new_day()
        
        # Определяем группу
        group = self.ACTION_GROUPS.get(action_id)
        if not group:
            return True  # Экшен без лимита
        
        # Проверка по кешу (быстро!)
        return not self.limits_reached[group]
    
    def record_usage(self, action_id: str):
        """
        Записать использование экшена (вызывается в КОНЦЕ экшена)
        
        Args:
            action_id: ID экшена
        """
        # Если заблокирован - не записываем
        if self.is_blocked:
            return
        
        group = self.ACTION_GROUPS.get(action_id)
        if not group:
            return
        
        # Увеличиваем счетчик
        self.counters[group] += 1
        
        # Пишем в ОБА лога
        self._write_log_entry(group)
        
        # Обновляем кеш лимита
        if self.counters[group] >= self.LIMITS[group]:
            self.limits_reached[group] = True
            logging.warning(f"⚠️ Лимит использований достигнут: {group.upper()} = {self.counters[group]}/{self.LIMITS[group]}")
    
    def _check_and_reset_if_new_day(self):
        """Проверить наступление нового дня МСК и сбросить счетчики"""
        today = self._get_msk_date()
        
        # Читаем последнюю запись из ОСНОВНЫХ логов
        records = self._read_logs(self.main_log_file)
        if not records:
            return
        
        last_date = records[-1]['date']
        
        # Если наступил новый день - сбрасываем счетчики
        if last_date != today:
            logging.info(f"🔄 Наступил новый день МСК ({today}), сброс счетчиков")
            self.counters = {'tp': 0, 'qb': 0}
            self.limits_reached = {'tp': False, 'qb': False}
            
            # Также снимаем блокировку
            if self.is_blocked:
                self.is_blocked = False
                self.block_reason = ""
                logging.info("✅ Блокировка снята (новый день)")
    
    def get_stats(self) -> dict:
        """
        Получить статистику использований
        
        Returns:
            dict: {group: {'used': int, 'limit': int, 'remaining': int, 'blocked': bool}, ...}
        """
        self._check_and_reset_if_new_day()
        self._check_decoy_integrity()
        
        stats = {}
        for group in self.counters:
            stats[group] = {
                'used': self.counters[group],
                'limit': self.LIMITS[group],
                'remaining': max(0, self.LIMITS[group] - self.counters[group]),
                'blocked': self.is_blocked
            }
        
        return stats