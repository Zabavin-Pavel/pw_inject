"""
Система лимитов использования экшенов с защитой от редактирования
"""
import hashlib
import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Часовой пояс МСК (UTC+3)
MSK = timezone(timedelta(hours=3))

class ActionLimiter:
    """Управление лимитами использования экшенов"""
    
    # Лимиты по группам экшенов
    LIMITS = {
        'tp': 200,     # NEXT/LONG (общий счетчик)
        'qb': 60,      # QBSO/QBGO (общий счетчик)
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
    
    def __init__(self, log_file_path: Path):
        """
        Args:
            log_file_path: путь к файлу логов использований
        """
        self.log_file = log_file_path
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
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
        
        # Инициализация при старте
        self._load_counters_from_logs()
    
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
    
    def _read_logs(self):
        """
        Прочитать и валидировать логи
        
        Returns:
            list: список валидных записей [{date, action_group, hash}, ...]
        """
        if not self.log_file.exists():
            return []
        
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            records = []
            prev_hash = ""
            
            for line in lines:
                line = line.strip()
                if not line:
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
            logging.error(f"Ошибка чтения логов: {e}")
            return []
    
    def _load_counters_from_logs(self):
        """Загрузить счетчики из логов при старте приложения"""
        records = self._read_logs()
        
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
        Записать использование экшена в лог
        
        Args:
            action_group: группа экшена ('tp' или 'qb')
        """
        records = self._read_logs()
        
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
        
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(record) + '\n')
        except Exception as e:
            logging.error(f"Ошибка записи в лог: {e}")
    
    def can_use(self, action_id: str) -> bool:
        """
        БЫСТРАЯ проверка: можно ли использовать экшен (из кеша)
        
        Args:
            action_id: ID экшена
        
        Returns:
            bool: True если можно использовать
        """
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
        group = self.ACTION_GROUPS.get(action_id)
        if not group:
            return
        
        # Увеличиваем счетчик
        self.counters[group] += 1
        
        # Пишем в лог
        self._write_log_entry(group)
        
        # Обновляем кеш лимита
        if self.counters[group] >= self.LIMITS[group]:
            self.limits_reached[group] = True
            logging.warning(f"⚠️ Лимит использований достигнут: {group.upper()} = {self.counters[group]}/{self.LIMITS[group]}")
    
    def _check_and_reset_if_new_day(self):
        """Проверить наступление нового дня МСК и сбросить счетчики"""
        today = self._get_msk_date()
        
        # Читаем последнюю запись из логов
        records = self._read_logs()
        if not records:
            return
        
        last_date = records[-1]['date']
        
        # Если наступил новый день - сбрасываем счетчики
        if last_date != today:
            logging.info(f"🔄 Наступил новый день МСК ({today}), сброс счетчиков")
            self.counters = {'tp': 0, 'qb': 0}
            self.limits_reached = {'tp': False, 'qb': False}
    
    def get_stats(self) -> dict:
        """
        Получить статистику использований
        
        Returns:
            dict: {group: {'used': int, 'limit': int, 'remaining': int}, ...}
        """
        self._check_and_reset_if_new_day()
        
        stats = {}
        for group in self.counters:
            stats[group] = {
                'used': self.counters[group],
                'limit': self.LIMITS[group],
                'remaining': max(0, self.LIMITS[group] - self.counters[group])
            }
        
        return stats