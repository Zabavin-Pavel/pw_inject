"""
Класс для работы с памятью процесса
Обновлен для поддержки записи
"""
import ctypes
from ctypes import wintypes
import logging
from win32_api import *

class Memory:
    """Управление памятью процесса"""
    
    def __init__(self):
        self.kernel32 = ctypes.windll.kernel32
        self.process_handle = None
        self.pid = None
        self.module_base = None
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def attach_by_pid(self, pid, module_name="ElementClient.exe"):
        """
        Подключиться к процессу по PID
        
        Args:
            pid: ID процесса
            module_name: Имя модуля
        
        Returns:
            bool: True если подключение успешно
        """
        self.pid = pid
        
        # Открываем процесс
        self.process_handle = self.kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
        if not self.process_handle:
            self.logger.error(f"Failed to open process {pid}")
            return False
        
        # Получаем базовый адрес модуля
        self.module_base = self._get_module_base(module_name)
        if self.module_base == 0:
            self.logger.error(f"Failed to get module base for {module_name}")
            return False
        
        self.logger.info(f"Attached to PID {pid}, module base: {hex(self.module_base)}")
        return True
    
    def _get_module_base(self, module_name):
        """Получить базовый адрес модуля"""
        snapshot = self.kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPMODULE, self.pid)
        me32 = MODULEENTRY32()
        me32.dwSize = ctypes.sizeof(MODULEENTRY32)
        
        if self.kernel32.Module32First(snapshot, ctypes.byref(me32)):
            while True:
                current_module = me32.szModule.decode('utf-8', errors='ignore')
                if current_module.lower() == module_name.lower():
                    base = ctypes.cast(me32.modBaseAddr, ctypes.c_void_p).value
                    self.kernel32.CloseHandle(snapshot)
                    return base
                
                if not self.kernel32.Module32Next(snapshot, ctypes.byref(me32)):
                    break
        
        self.kernel32.CloseHandle(snapshot)
        return 0
    
    def read_int(self, address):
        """Прочитать 4-байтовое целое число с проверкой"""
        try:
            buffer = ctypes.c_int()
            bytes_read = ctypes.c_size_t()
            
            result = self.kernel32.ReadProcessMemory(
                self.process_handle,
                ctypes.c_void_p(address),
                ctypes.byref(buffer),
                4,
                ctypes.byref(bytes_read)
            )
            
            if not result or bytes_read.value != 4:
                return None
            
            return buffer.value
        except:
            return None

    def read_uint(self, address):
        """Прочитать 4-байтовое беззнаковое целое число с проверкой"""
        try:
            buffer = ctypes.c_uint32()
            bytes_read = ctypes.c_size_t()
            
            result = self.kernel32.ReadProcessMemory(
                self.process_handle,
                ctypes.c_void_p(address),
                ctypes.byref(buffer),
                4,
                ctypes.byref(bytes_read)
            )
            
            if not result or bytes_read.value != 4:
                return None
            
            return buffer.value
        except:
            return None

    def read_uint64(self, address):
        """Прочитать 8-байтовое целое число с проверкой"""
        try:
            buffer = ctypes.c_uint64()
            bytes_read = ctypes.c_size_t()
            
            result = self.kernel32.ReadProcessMemory(
                self.process_handle,
                ctypes.c_void_p(address),
                ctypes.byref(buffer),
                8,
                ctypes.byref(bytes_read)
            )
            
            if not result or bytes_read.value != 8:
                return None
            
            return buffer.value
        except:
            return None
    
    def read_float(self, address):
        """Прочитать float с проверкой"""
        try:
            buffer = ctypes.c_float()
            bytes_read = ctypes.c_size_t()
            
            result = self.kernel32.ReadProcessMemory(
                self.process_handle,
                ctypes.c_void_p(address),
                ctypes.byref(buffer),
                4,
                ctypes.byref(bytes_read)
            )
            
            if not result or bytes_read.value != 4:
                return None
            
            return buffer.value
        except:
            return None
    
    def read_byte(self, address):
        """Прочитать 1 байт"""
        try:
            buffer = ctypes.c_byte()
            bytes_read = ctypes.c_size_t()
            
            result = self.kernel32.ReadProcessMemory(
                self.process_handle,
                ctypes.c_void_p(address),
                ctypes.byref(buffer),
                1,
                ctypes.byref(bytes_read)
            )
            
            if not result or bytes_read.value != 1:
                return None
            
            return buffer.value
        except:
            return None
    
    def read_string(self, address, max_length=256, encoding='utf-16-le'):
        """Прочитать строку"""
        try:
            if encoding == 'utf-16-le':
                buffer = (ctypes.c_wchar * max_length)()
                bytes_to_read = max_length * 2
            else:
                buffer = (ctypes.c_char * max_length)()
                bytes_to_read = max_length
            
            bytes_read = ctypes.c_size_t()
            
            result = self.kernel32.ReadProcessMemory(
                self.process_handle,
                ctypes.c_void_p(address),
                buffer,
                bytes_to_read,
                ctypes.byref(bytes_read)
            )
            
            if not result:
                return None
            
            if encoding == 'utf-16-le':
                # Для Unicode строк
                text = ''.join(buffer).split('\x00')[0]
            else:
                # Для ASCII строк
                text = buffer.value.decode(encoding, errors='ignore')
            
            return text
        except Exception as e:
            self.logger.error(f"Failed to read string at {hex(address)}: {e}")
            return None
    
    def write_int(self, address, value):
        """Записать 4-байтовое целое число"""
        try:
            buffer = ctypes.c_int(value)
            bytes_written = ctypes.c_size_t()
            
            result = self.kernel32.WriteProcessMemory(
                self.process_handle,
                ctypes.c_void_p(address),
                ctypes.byref(buffer),
                4,
                ctypes.byref(bytes_written)
            )
            
            return result and bytes_written.value == 4
        except:
            return False
    
    def write_float(self, address, value):
        """Записать float"""
        try:
            buffer = ctypes.c_float(value)
            bytes_written = ctypes.c_size_t()
            
            result = self.kernel32.WriteProcessMemory(
                self.process_handle,
                ctypes.c_void_p(address),
                ctypes.byref(buffer),
                4,
                ctypes.byref(bytes_written)
            )
            
            return result and bytes_written.value == 4
        except:
            return False
    
    def write_byte(self, address, value):
        """Записать 1 байт"""
        try:
            buffer = ctypes.c_byte(value)
            bytes_written = ctypes.c_size_t()
            
            result = self.kernel32.WriteProcessMemory(
                self.process_handle,
                ctypes.c_void_p(address),
                ctypes.byref(buffer),
                1,
                ctypes.byref(bytes_written)
            )
            
            return result and bytes_written.value == 1
        except:
            return False
    
    def is_valid(self):
        """Проверка что процесс еще жив"""
        if not self.process_handle:
            return False
        
        exit_code = wintypes.DWORD()
        if self.kernel32.GetExitCodeProcess(self.process_handle, ctypes.byref(exit_code)):
            # STILL_ACTIVE = 259
            return exit_code.value == 259
        
        return False
    
    def close(self):
        """Закрыть хендл процесса"""
        if self.process_handle:
            self.kernel32.CloseHandle(self.process_handle)
            self.process_handle = None
            self.pid = None
            self.module_base = None