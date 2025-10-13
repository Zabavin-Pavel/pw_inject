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

    def freeze_address(self, address, value, value_type='int32', interval=0.01):
        """
        Заморозить адрес - постоянно записывать значение
        
        Args:
            address: адрес для заморозки
            value: значение для записи
            value_type: тип данных ('int32', 'float', 'byte')
            interval: интервал обновления в секундах
        
        Returns:
            dict: информация о заморозке для последующей разморозки
        """
        import threading
        import time
        
        freeze_info = {
            'active': True,
            'thread': None,
            'address': address,
            'value': value,
            'type': value_type
        }
        
        def freeze_loop():
            while freeze_info['active']:
                if value_type == 'int32':
                    self.write_int(address, value)
                elif value_type == 'float':
                    self.write_float(address, value)
                elif value_type == 'byte':
                    self.write_byte(address, value)
                time.sleep(interval)
        
        freeze_info['thread'] = threading.Thread(target=freeze_loop, daemon=True)
        freeze_info['thread'].start()
        
        return freeze_info

    def unfreeze_address(self, freeze_info):
        """
        Разморозить адрес
        
        Args:
            freeze_info: информация о заморозке из freeze_address()
        """
        freeze_info['active'] = False
        if freeze_info['thread']:
            freeze_info['thread'].join(timeout=1)









    def write_uint64(self, address, value):
        """Записать 8-байтовое целое число"""
        try:
            buffer = ctypes.c_uint64(value)
            bytes_written = ctypes.c_size_t()
            
            result = self.kernel32.WriteProcessMemory(
                self.process_handle,
                ctypes.c_void_p(address),
                ctypes.byref(buffer),
                8,
                ctypes.byref(bytes_written)
            )
            
            return result and bytes_written.value == 8
        except:
            return False


    def allocate_memory(self, size):
        """Выделить память в процессе"""
        try:
            MEM_COMMIT = 0x1000
            MEM_RESERVE = 0x2000
            PAGE_EXECUTE_READWRITE = 0x40
            
            address = self.kernel32.VirtualAllocEx(
                self.process_handle,
                None,
                size,
                MEM_COMMIT | MEM_RESERVE,
                PAGE_EXECUTE_READWRITE
            )
            
            if address:
                self.logger.info(f"Memory allocated at {hex(address)}, size: {size}")
                return address
            else:
                self.logger.error("Failed to allocate memory")
                return None
        except Exception as e:
            self.logger.error(f"Exception in allocate_memory: {e}")
            return None

    def free_memory(self, address):
        """Освободить память в процессе"""
        try:
            MEM_RELEASE = 0x8000
            result = self.kernel32.VirtualFreeEx(
                self.process_handle,
                address,
                0,
                MEM_RELEASE
            )
            if result:
                self.logger.info(f"Memory freed at {hex(address)}")
            return result
        except Exception as e:
            self.logger.error(f"Exception in free_memory: {e}")
            return False

    def write_bytes(self, address, data):
        """Записать массив байтов"""
        try:
            buffer = (ctypes.c_byte * len(data))(*data)
            bytes_written = ctypes.c_size_t()
            
            result = self.kernel32.WriteProcessMemory(
                self.process_handle,
                ctypes.c_void_p(address),
                buffer,
                len(data),
                ctypes.byref(bytes_written)
            )
            
            if result and bytes_written.value == len(data):
                return True
            else:
                self.logger.error(f"Failed to write bytes at {hex(address)}")
                return False
        except Exception as e:
            self.logger.error(f"Exception in write_bytes: {e}")
            return False

    def create_remote_thread(self, start_address, parameter=0):
        """Создать поток в удалённом процессе"""
        try:
            thread_id = ctypes.c_ulong()
            
            thread_handle = self.kernel32.CreateRemoteThread(
                self.process_handle,
                None,
                0,
                start_address,
                parameter,
                0,
                ctypes.byref(thread_id)
            )
            
            if thread_handle:
                self.logger.info(f"Remote thread created: {hex(thread_handle)}, TID: {thread_id.value}")
                # Ждём завершения потока
                self.kernel32.WaitForSingleObject(thread_handle, 5000)  # 5 секунд таймаут
                self.kernel32.CloseHandle(thread_handle)
                return True
            else:
                self.logger.error("Failed to create remote thread")
                return False
        except Exception as e:
            self.logger.error(f"Exception in create_remote_thread: {e}")
            return False

    def call_function(self, func_offset, args):
        """
        Вызвать функцию в игре через shellcode
        
        Args:
            func_offset: оффсет функции от базы модуля
            args: список аргументов (до 4-х для x64 fastcall)
        
        Returns:
            bool: успешность вызова
        """
        if not self.module_base:
            self.logger.error("Module base not set")
            return False
        
        func_address = self.module_base + func_offset
        
        # x64 fastcall: первые 4 аргумента в rcx, rdx, r8, r9
        # Создаём shellcode для вызова функции
        shellcode = self._generate_call_shellcode(func_address, args)
        
        # Выделяем память для shellcode
        shellcode_addr = self.allocate_memory(len(shellcode))
        if not shellcode_addr:
            return False
        
        # Записываем shellcode
        if not self.write_bytes(shellcode_addr, shellcode):
            self.free_memory(shellcode_addr)
            return False
        
        # Запускаем shellcode
        success = self.create_remote_thread(shellcode_addr)
        
        # Освобождаем память
        self.free_memory(shellcode_addr)
        
        return success

    def _generate_call_shellcode(self, func_address, args):
        """
        Генерировать x64 shellcode для вызова функции
        
        Shellcode структура:
        1. Сохранить регистры
        2. Загрузить аргументы в rcx, rdx, r8, r9
        3. Вызвать функцию
        4. Восстановить регистры
        5. Вернуться
        """
        shellcode = []
        
        # push rbp
        shellcode.extend([0x55])
        # mov rbp, rsp
        shellcode.extend([0x48, 0x89, 0xE5])
        # sub rsp, 0x20 (выделяем shadow space)
        shellcode.extend([0x48, 0x83, 0xEC, 0x20])
        
        # Загружаем аргументы
        if len(args) > 0:
            # mov rcx, arg0
            arg0 = args[0] & 0xFFFFFFFFFFFFFFFF
            shellcode.extend([0x48, 0xB9])  # movabs rcx
            shellcode.extend(arg0.to_bytes(8, 'little'))
        
        if len(args) > 1:
            # mov rdx, arg1
            arg1 = args[1] & 0xFFFFFFFFFFFFFFFF
            shellcode.extend([0x48, 0xBA])  # movabs rdx
            shellcode.extend(arg1.to_bytes(8, 'little'))
        
        if len(args) > 2:
            # mov r8, arg2
            arg2 = args[2] & 0xFFFFFFFFFFFFFFFF
            shellcode.extend([0x49, 0xB8])  # movabs r8
            shellcode.extend(arg2.to_bytes(8, 'little'))
        
        if len(args) > 3:
            # mov r9, arg3
            arg3 = args[3] & 0xFFFFFFFFFFFFFFFF
            shellcode.extend([0x49, 0xB9])  # movabs r9
            shellcode.extend(arg3.to_bytes(8, 'little'))
        
        # Если есть 5-й аргумент, кладём его в стек
        if len(args) > 4:
            arg4 = args[4] & 0xFFFFFFFF
            # mov dword ptr [rsp+0x20], arg4
            shellcode.extend([0xC7, 0x44, 0x24, 0x20])
            shellcode.extend(arg4.to_bytes(4, 'little'))
        
        # Вызываем функцию
        # mov rax, func_address
        shellcode.extend([0x48, 0xB8])
        shellcode.extend(func_address.to_bytes(8, 'little'))
        # call rax
        shellcode.extend([0xFF, 0xD0])
        
        # Восстанавливаем стек
        # add rsp, 0x20
        shellcode.extend([0x48, 0x83, 0xC4, 0x20])
        # pop rbp
        shellcode.extend([0x5D])
        # ret
        shellcode.extend([0xC3])
        
        return shellcode
















