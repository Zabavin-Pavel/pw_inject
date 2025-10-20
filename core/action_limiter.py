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
    
    # Лимиты по типам точек
    LIMITS = {
        'FROST': 200,  # FROST точки (NEXT/LONG)
        'QB': 100,     # QB точки (QB SO/GO)
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
            'FROST': 0,
            'QB': 0,
        }
        
        # Кеш состояния лимитов
        self.limits_reached = {
            'FROST': False,
            'QB': False,
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
            list: список валидных записей или []
        """
        if not log_file.exists():
            return []
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            # Если файл пустой
            if not content:
                return []
            
            # Пытаемся распарсить как JSON массив
            try:
                records = json.loads(content)
            except json.JSONDecodeError:
                # Возможно файл поврежден - пересоздаем
                logging.warning(f"⚠️ Log file {log_file} is corrupted, recreating...")
                log_file.unlink()
                return []
            
            # Валидация цепочки хешей
            prev_hash = ""
            valid_records = []
            
            for record in records:
                if not isinstance(record, dict):
                    continue
                
                # Проверяем необходимые ключи (поддержка старого и нового формата)
                if 'date' not in record or 'hash' not in record:
                    continue
                
                # ОБРАТНАЯ СОВМЕСТИМОСТЬ: поддержка обоих форматов
                action_group = record.get('action_group') or record.get('action')
                
                if not action_group:
                    continue
                
                # Проверяем хеш
                date = record['date']
                data = f"{date}:{action_group}"
                expected_hash = self._compute_hash(data, prev_hash)
                
                if record['hash'] != expected_hash:
                    # Цепочка нарушена - ТРЕВОГА!
                    logging.error(f"🚨 HASH MISMATCH detected in {log_file}")
                    self.is_blocked = True
                    self.block_reason = "Log tampering detected"
                    return []
                
                # Нормализуем запись к новому формату
                normalized_record = {
                    'date': date,
                    'action_group': action_group,
                    'hash': record['hash']
                }
                
                valid_records.append(normalized_record)
                prev_hash = record['hash']
            
            return valid_records
        
        except Exception as e:
            logging.error(f"Failed to read logs: {e}")
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
        """Загрузить счетчики из основных логов"""
        records = self._read_logs(self.main_log_file)
        
        if not records:
            return
        
        today = self._get_msk_date()
        
        # Считаем использования за сегодня
        for record in records:
            if record['date'] == today:
                # ИСПРАВЛЕНИЕ: поддержка старого формата логов
                point_type = record.get('action_group') or record.get('action')
                
                if point_type and point_type in self.counters:
                    self.counters[point_type] += 1
        
        # Обновляем состояние лимитов
        for point_type in self.counters:
            if self.counters[point_type] >= self.LIMITS[point_type]:
                self.limits_reached[point_type] = True
        
        logging.info(f"📊 Загружены счетчики: FROST={self.counters['FROST']}/{self.LIMITS['FROST']}, QB={self.counters['QB']}/{self.LIMITS['QB']}")
    
    def _write_log_entry(self, point_type: str):
        """
        Записать запись об использовании в ОБА лога
        
        Args:
            point_type: тип точки ("FROST" или "QB")
        """
        # Записываем в основной лог
        self._append_to_log(self.main_log_file, point_type)
        
        # Записываем в приманку
        self._append_to_log(self.decoy_log_file, point_type)
    
    def _append_to_log(self, log_file: Path, point_type: str):
        """
        Добавить запись в лог-файл
        
        Args:
            log_file: путь к файлу
            point_type: тип точки ("FROST" или "QB")
        """
        # Читаем существующие записи для получения предыдущего хеша
        records = self._read_logs(log_file)
        prev_hash = records[-1]['hash'] if records else ""
        
        # Создаем новую запись
        date = self._get_msk_date()
        data = f"{date}:{point_type}"
        hash_value = self._compute_hash(data, prev_hash)
        
        new_record = {
            'date': date,
            'action_group': point_type,  # НОВЫЙ КЛЮЧ
            'hash': hash_value
        }
        
        # Добавляем в файл
        try:
            if log_file.exists():
                with open(log_file, 'r', encoding='utf-8') as f:
                    existing_records = json.load(f)
            else:
                existing_records = []
            
            existing_records.append(new_record)
            
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(existing_records, f, indent=2, ensure_ascii=False)
        
        except Exception as e:
            logging.error(f"Failed to write log entry: {e}")

    def can_use(self, point_type: str) -> bool:
        """
        Проверить можно ли использовать точку данного типа
        
        Args:
            point_type: тип точки ("FROST" или "QB")
        
        Returns:
            bool: True если можно использовать
        """
        # Если заблокирован - запрещаем все
        if self.is_blocked:
            return False
        
        # Проверяем смену дня
        self._check_and_reset_if_new_day()
        
        # Проверяем целостность приманки
        self._check_decoy_integrity()
        
        # Проверяем лимит для данного типа
        if point_type not in self.LIMITS:
            return True  # Неизвестный тип - разрешаем
        
        return not self.limits_reached.get(point_type, False)
    
    def record_usage(self, point_type: str):
        """
        Записать использование точки
        
        Args:
            point_type: тип точки ("FROST" или "QB")
        """
        # Если заблокирован - не записываем
        if self.is_blocked:
            return
        
        if point_type not in self.LIMITS:
            return
        
        # Увеличиваем счетчик
        self.counters[point_type] += 1
        
        # Пишем в ОБА лога
        self._write_log_entry(point_type)
        
        # Обновляем кеш лимита
        if self.counters[point_type] >= self.LIMITS[point_type]:
            self.limits_reached[point_type] = True
            logging.warning(f"⚠️ Лимит использований достигнут: {point_type} = {self.counters[point_type]}/{self.LIMITS[point_type]}")
    
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
            self.counters = {'FROST': 0, 'QB': 0}
            self.limits_reached = {'FROST': False, 'QB': False}
            
            # Также снимаем блокировку
            if self.is_blocked:
                self.is_blocked = False
                self.block_reason = ""
                logging.info("✅ Блокировка снята (новый день)")
    
    def get_stats(self) -> dict:
        """
        Получить статистику использований
        
        Returns:
            dict: {point_type: {'used': int, 'limit': int, 'remaining': int, 'blocked': bool}, ...}
        """
        self._check_and_reset_if_new_day()
        self._check_decoy_integrity()
        
        stats = {}
        for point_type in self.counters:
            stats[point_type] = {
                'used': self.counters[point_type],
                'limit': self.LIMITS[point_type],
                'remaining': max(0, self.LIMITS[point_type] - self.counters[point_type]),
                'blocked': self.is_blocked
            }
        
        return stats