"""
Главное окно приложения - ОБНОВЛЕНО
Добавлена интеграция с ActionLimiter
"""
import tkinter as tk
from PIL import Image, ImageTk
import logging
import sys
import pystray
from pystray import MenuItem as item
import threading
import ctypes
from ctypes import wintypes
import math
from pathlib import Path

from gui.styles import *
from gui.character_panel import CharacterPanel
from gui.hotkey_panel import HotkeyPanel
from core import AppState, ActionManager, HotkeyManager
from core.keygen import PERMISSION_NONE, PERMISSION_TRY, PERMISSION_PRO, PERMISSION_DEV
from core.action_limiter import ActionLimiter
from ahk_local.manager import AHKManager
from actions import (
    register_toggle_actions,
    register_try_actions,
    register_pro_actions,
    register_dev_actions,
    follow_loop_callback,
    attack_loop_callback,
)

# Константа для интервала toggle экшенов
TOGGLE_ACTION_INTERVALS = {
    'follow': 500,      # 0.5 секунды
    'attack': 2000,      # 0.5 секунды  
    'headhunter': 200,  # 0.2 секунды
}

class MainWindow:
    """Главное окно - координатор"""
    
    def __init__(self, multibox_manager, settings_manager, app_hub, license_level):
        self.manager = multibox_manager
        self.settings_manager = settings_manager
        
        # Сохраняем ссылку на AppHub
        self.app_hub = app_hub
        
        # НОВОЕ: Сохраняем уровень лицензии (уже проверенный)
        self.license_level = license_level
        
        # Предыдущий уровень доступа (для оптимизации UI)
        self.prev_permission_level = PERMISSION_NONE
        
        # Состояние приложения
        self.app_state = AppState()
        
        # НОВОЕ: Сразу устанавливаем уровень доступа из лицензии
        self.app_state.verified = True
        self.app_state.permission_level = license_level.lower()  # <-- .lower()
        self.prev_permission_level = license_level.lower()  # <-- .lower()
        
        logging.info(f"🔑 Permission level set: {license_level.lower()}")
        
        # ActionLimiter
        self.action_limiter = ActionLimiter()
        
        # Менеджеры
        self.action_manager = ActionManager(self.app_state)
        self.hotkey_manager = HotkeyManager(
            self.action_manager,
            on_hotkey_executed=self._on_hotkey_flash
        )
        
        # AHK менеджер
        self.ahk_manager = AHKManager()
        
        # Таймеры для toggle экшенов
        self.action_timers = {}
        
        # Регистрируем действия
        self._register_actions()
        
        # НОВОЕ: Загрузить хоткеи ПЕРЕД созданием UI
        self._load_hotkeys()
        
        # Создать UI (теперь HotkeyPanel сразу увидит загруженные хоткеи)
        self._create_ui()
        
        # Создать tray icon
        self._create_tray_icon()
        
        # Применить topmost из настроек
        self.is_topmost = self.settings_manager.is_topmost()
        self.root.attributes('-topmost', self.is_topmost)
        
        # Запустить polling активного окна
        self._start_active_window_polling()
        
        # Передаем зависимости в multibox_manager
        self.manager.set_ahk_manager(self.ahk_manager)
        self.manager.set_app_state(self.app_state)
        self.manager.set_action_limiter(self.action_limiter)

        # Делаем первоначальную загрузку через _silent_refresh
        self._silent_refresh()

        # Запустить периодическое обновление цветов
        self.root.after(500, self._update_party_colors)

    def _register_actions(self):
            """Зарегистрировать все действия (ОБНОВЛЕНО)"""
            
            # ИСПРАВЛЕНО: Toggle действия - передаем self для доступа к _start_action_loop/_stop_action_loop
            register_toggle_actions(
                self.action_manager,
                self.manager,
                self.ahk_manager,
                self.app_state,
                self  # НОВОЕ: передаем main_window
            )
            
            # TRY уровень (LBM, SPACE, follow_leader) - ИСПРАВЛЕНО: передаем app_state
            register_try_actions(
                self.action_manager,
                self.ahk_manager,
                self.app_state,  # НОВОЕ: для получения PIDs группы
                self.manager
            )
            
            # PRO уровень (TARGET, NEXT >>, <- LONG, LONG ->, FINAL ->)
            register_pro_actions(
                self.action_manager,
                self.manager,
                self.app_state,
                self.action_limiter
            )
            
            # DEV уровень (ACT SO, ACT GO)
            register_dev_actions(
                self.action_manager,
                self.manager,
                self.app_state,
                self.action_limiter
            )

    def _create_ui(self):
        """Создать UI"""
        self.root = tk.Tk()
        self.root.title("Discord")
    
        # === ЗАГРУЗИТЬ ПОЗИЦИЮ ИЗ НАСТРОЕК ===
        pos = self.settings_manager.get_window_position()
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{pos['x']}+{pos['y']}")
        
        self.root.configure(bg=COLOR_BG)
        
        # Убрать стандартную рамку окна
        self.root.overrideredirect(True)
        
        # Обработчик закрытия
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # === TITLE BAR (кастомная) ===
        self.title_bar = tk.Frame(self.root, bg=COLOR_BG, height=40)
        self.title_bar.pack(fill=tk.X, side=tk.TOP)
        self.title_bar.pack_propagate(False)
        
        # Иконка + название (слева)
        try:
            icon_image = Image.open(TRAY_ICON_PATH)
            icon_image = icon_image.resize((18, 18), Image.Resampling.LANCZOS)
            self.app_icon = ImageTk.PhotoImage(icon_image)
            icon_label = tk.Label(self.title_bar, image=self.app_icon, bg=COLOR_BG)
            icon_label.pack(side=tk.LEFT, padx=(10, 5))
        except:
            pass
        
        title_label = tk.Label(
            self.title_bar,
            text="Xvocmuk",
            font=FONT_TITLE,
            bg=COLOR_BG,
            fg=COLOR_TEXT
        )
        title_label.pack(side=tk.LEFT, padx=0)
        
        # Кнопки управления окном (ИСПРАВЛЕНО - выравнивание и отступы)
        # ПОРЯДОК: Pin, Minimize, Close (БЕЗ Refresh)

        # Кнопка Close (ТРЕТЬЯ)
        self.close_btn = tk.Label(
            self.title_bar,
            text="✕",
            font=("Segoe UI", 14, "bold"),
            bg=COLOR_BG,
            fg=COLOR_TEXT,
            cursor="hand2",
            width=2,
            height=1,
            anchor="center"
        )
        self.close_btn.pack(side=tk.RIGHT, padx=(0, 10))
        self.close_btn.bind("<Button-1>", lambda e: self.on_close())
        self.close_btn.bind("<Enter>", lambda e: self.close_btn.configure(fg=COLOR_ACCENT))
        self.close_btn.bind("<Leave>", lambda e: self.close_btn.configure(fg=COLOR_TEXT))

        # Кнопка Minimize (ВТОРАЯ)
        self.minimize_btn = tk.Label(
            self.title_bar,
            text="−",
            font=("Segoe UI", 14, "bold"),
            bg=COLOR_BG,
            fg=COLOR_TEXT,
            cursor="hand2",
            width=2,
            height=1,
            anchor="center"
        )
        self.minimize_btn.pack(side=tk.RIGHT, padx=0)
        self.minimize_btn.bind("<Button-1>", lambda e: self.minimize_to_tray())
        self.minimize_btn.bind("<Enter>", lambda e: self.minimize_btn.configure(fg=COLOR_ACCENT))
        self.minimize_btn.bind("<Leave>", lambda e: self.minimize_btn.configure(fg=COLOR_TEXT))

        # Кнопка Pin (ПЕРВАЯ)
        self.pin_btn = tk.Label(
            self.title_bar,
            text="📌",
            font=("Segoe UI", 10),
            bg=COLOR_BG,
            fg=COLOR_TEXT if not self.settings_manager.is_topmost() else COLOR_ACCENT,
            cursor="hand2",
            width=2,
            height=1,
            anchor="center"
        )
        self.pin_btn.pack(side=tk.RIGHT, padx=0)
        self.pin_btn.bind("<Button-1>", lambda e: self.toggle_topmost())
        self.pin_btn.bind("<Enter>", lambda e: self.pin_btn.configure(fg=COLOR_ACCENT_HOVER))
        self.pin_btn.bind("<Leave>", lambda e: self.pin_btn.configure(
            fg=COLOR_ACCENT if self.is_topmost else COLOR_TEXT
        ))
        
        # Drag window - привязка к title bar
        self.title_bar.bind("<Button-1>", self._start_drag)
        self.title_bar.bind("<B1-Motion>", self._do_drag)
        title_label.bind("<Button-1>", self._start_drag)
        title_label.bind("<B1-Motion>", self._do_drag)
        
        # === MAIN CONTENT ===
        content_frame = tk.Frame(self.root, bg=COLOR_BG)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))  # ← pady=(0, 5)
        
        # Левая панель: персонажи (ФИКСИРОВАННАЯ ШИРИНА + РАМКА)
        left_container = tk.Frame(
            content_frame, 
            bg=COLOR_BG, 
            width=CHARACTERS_PANEL_WIDTH,
            highlightthickness=1,
            highlightbackground=COLOR_BORDER
        )
        left_container.pack(side=tk.LEFT, fill=tk.Y, expand=False, padx=0)  # ← padx=0 вместо padx=(0, 10)
        left_container.pack_propagate(False)
        
        self.character_panel = CharacterPanel(
            left_container,
            self.app_state,
            on_character_selected=None,  # УДАЛЕНО: toggle выбора больше не нужен
            on_character_toggled=self.on_character_toggled
        )
        self.character_panel.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        
        # Правая панель: хоткеи + иконки действий (С РАМКОЙ)
        self.right_container = tk.Frame(
            content_frame,
            bg=COLOR_BG,
            highlightthickness=1,
            highlightbackground=COLOR_BORDER
        )
        self.right_container.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.hotkey_panel = HotkeyPanel(
            self.right_container,
            self.app_state,
            self.action_manager,
            self.hotkey_manager,
            self.settings_manager,
            on_action_executed=self.on_action_executed
        )
        self.hotkey_panel.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
                
        # ОТЛАДКА
        logging.info(f"📋 HotkeyPanel created, actions count: {len(self.action_manager.get_hotkey_actions())}")

    def _on_hotkey_flash(self, action_id: str):
        """Callback для мигания UI при срабатывании хоткея"""
        # Вызываем в главном потоке GUI
        self.root.after(0, lambda: self.hotkey_panel.flash_action(action_id))

    def _setup_hotkey_flash(self):
        """Настроить мигание при вызове хоткеев"""
        # Переопределить обработчик хоткеев
        original_handler = self.hotkey_manager._on_hotkey_pressed
        
        def new_handler(action_id: str):
            # Выполнить действие
            self.action_manager.execute(action_id)
            
            # Мигнуть в UI
            self.hotkey_panel.flash_action(action_id)
        
        self.hotkey_manager._on_hotkey_pressed = new_handler
    
    def _start_drag(self, event):
        """Начать перетаскивание окна"""
        self._drag_start_x = event.x
        self._drag_start_y = event.y
    
    def _do_drag(self, event):
        """Перетаскивание окна"""
        x = self.root.winfo_x() + event.x - self._drag_start_x
        y = self.root.winfo_y() + event.y - self._drag_start_y
        self.root.geometry(f"+{x}+{y}")
    
    def minimize_to_tray(self):
        """Свернуть в трей"""
        self.root.withdraw()
    
    def toggle_topmost(self):
        """Переключить режим поверх всех окон"""
        self.is_topmost = not self.is_topmost
        
        self.settings_manager.set_topmost(self.is_topmost)
        self.root.attributes('-topmost', self.is_topmost)
        
        # Обновить цвет кнопки
        self.pin_btn.configure(fg=COLOR_ACCENT if self.is_topmost else COLOR_TEXT)
    
    def _create_tray_icon(self):
        """Создать иконку в трее"""
        try:
            image = Image.open(TRAY_ICON_PATH)
            
            menu = pystray.Menu(
                item('Show', self._show_window, default=True),  # default=True !
                item('Always on Top', self._toggle_topmost_from_tray, 
                    checked=lambda item: self.settings_manager.is_topmost()),
                item('Exit', self._exit_from_tray)
            )
            
            self.tray_icon = pystray.Icon("pw_bot", image, "Xvocmuk", menu)
            
            # Запустить в отдельном потоке
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
            
            logging.info("Иконка трея создана")
        except Exception as e:
            logging.error(f"Failed to create tray icon: {e}")

    def _show_window(self, icon=None, item=None):
        """Показать окно из трея"""
        self.root.after(0, lambda: self.root.deiconify())
        self.root.after(50, lambda: self.root.lift())
        self.root.after(100, lambda: self.root.focus_force())
    
    def _toggle_topmost_from_tray(self):
        """Переключить topmost из трея"""
        self.toggle_topmost()
    
    def _exit_from_tray(self):
        """Выход из трея"""
        self.on_close()
    
    def _load_hotkeys(self):
        """Загрузить хоткеи из настроек"""
        hotkeys = self.settings_manager.get_hotkeys()
        
        for action_id, hotkey in hotkeys.items():
            if hotkey and hotkey != "-":
                try:
                    self.hotkey_manager.bind(hotkey, action_id)
                except Exception as e:
                    logging.warning(f"Не удалось загрузить хоткей {hotkey}: {e}")
    
    def _save_hotkeys(self):
        """Сохранить хоткеи в настройки"""
        hotkeys = {}
        
        for action_id, action in self.action_manager.actions.items():
            if action.has_hotkey:
                hotkey = self.hotkey_manager.get_hotkey_for_action(action_id)
                hotkeys[action_id] = hotkey if hotkey else "-"
        
        self.settings_manager.set_hotkeys(hotkeys)

    def on_character_selected(self, character):
        """Обработчик клика по никнейму персонажа - toggle выбора"""
        # Если этот персонаж уже выбран - снять выбор
        pass
        # if self.app_state.selected_character == character:
        #     self.app_state.select_character(None)
        # else:
        #     # Иначе - выбрать его
        #     self.app_state.select_character(character)
        
        # # Обновить отображение
        # self.character_panel.update_display()
    
    def on_character_toggled(self, character):
        """Обработчик переключения активности персонажа (чекбокс)"""
        pass
    
    def on_action_executed(self, action_id: str):
        """Обработчик выполнения действия"""
        self.action_manager.execute(action_id)
        
        # Мигнуть действием в HotkeyPanel
        self.hotkey_panel.flash_action(action_id)
    

    def on_close(self):
        """Закрытие приложения"""
        try:
            # Остановить AHK
            if hasattr(self, 'ahk_manager'):
                self.ahk_manager.stop()
                
            # ВАЖНО: Остановить keyboard hook
            if hasattr(self, 'hotkey_manager'):
                self.hotkey_manager.stop()
 
            
            # Сохранить позицию окна
            x = self.root.winfo_x()
            y = self.root.winfo_y()
            self.settings_manager.set_window_position(x, y)
            
            # Закрыть tray icon
            if self.tray_icon:
                self.tray_icon.stop()
            
            # Закрыть процессы памяти
            for char in self.manager.characters.values():
                if hasattr(char, 'memory'):
                    char.memory.close()
            
            logging.info("=== Завершение приложения ===")
            
            self.root.quit()
            self.root.destroy()
            
        except Exception as e:
            logging.error(f"Error during shutdown: {e}")
            import sys
            sys.exit(0)

    # ============================================
    # ДЕЙСТВИЯ (CALLBACKS)
    # ============================================
    
    def _start_action_loop(self, action_id: str, callback):
        """Запустить циклический вызов callback для toggle экшена"""
        interval = TOGGLE_ACTION_INTERVALS.get(action_id, 500)
        
        def loop():
            if self.app_state.is_action_active(action_id):
                try:
                    callback()
                except Exception as e:
                    logging.error(f"Error in {action_id} loop: {e}")
                
                # Повторить через соответствующий интервал
                self.action_timers[action_id] = self.root.after(interval, loop)
        
        loop()
    
    def _stop_action_loop(self, action_id: str):
        """Остановить циклический вызов"""
        if action_id in self.action_timers:
            timer_id = self.action_timers[action_id]
            if timer_id:
                try:
                    self.root.after_cancel(timer_id)
                except:
                    pass
            self.action_timers[action_id] = None
    
    def _follow_loop_callback(self):
        """Callback для Follow loop"""
        active_corrections = self.manager.follow_leader()
        if active_corrections > 0:
            logging.debug(f"Follow: {active_corrections} active corrections")

    def toggle_attack(self):
        """Toggle: Атака (копирование таргета лидера)"""
        is_active = self.app_state.is_action_active('attack')
        
        if is_active:
            print("Attack: STARTED")
            self._start_action_loop('attack', lambda: attack_loop_callback(self.manager))
        else:
            print("Attack: STOPPED")
            self._stop_action_loop('attack')
        
        self.hotkey_panel.update_display()

    def _attack_loop_callback(self):
        """Callback для Attack loop"""
        success_count = self.manager.set_attack_target()
        if success_count > 0:
            logging.debug(f"Attack: {success_count} targets set")
    
    def toggle_headhunter(self):
        """Toggle: Headhunter (Tab + ЛКМ по 100, 100)"""
        is_active = self.app_state.is_action_active('headhunter')
        
        if is_active:
            print("Headhunter: STARTED")
            # НОВОЕ: вызываем AHK, а не Python loop
            self.ahk_manager.start_headhunter()
        else:
            print("Headhunter: STOPPED")
            # НОВОЕ: останавливаем AHK
            self.ahk_manager.stop_headhunter()
        
        self.hotkey_panel.update_display()
    
    def run(self):
        """Запустить главный цикл"""
        self.root.mainloop()

    def start_instance_listener(self):
        """Запустить слушатель для сигналов от других экземпляров"""
        import socket
        
        def listener():
            try:
                server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                server.bind(('127.0.0.1', 47200))
                server.listen(1)
                
                while True:
                    try:
                        client, addr = server.accept()
                        data = client.recv(1024)
                        
                        if data == b'SHOW_WINDOW':
                            # Показать окно в главном потоке
                            self.root.after(0, self._show_window)
                        
                        client.close()
                    except:
                        break
            except:
                pass
        
        threading.Thread(target=listener, daemon=True).start()


    def _start_active_window_polling(self):
        """Запустить мониторинг активного окна ElementClient.exe"""
        def poll():
            try:
                # НОВОЕ: Сначала проверяем валидность текущего активного персонажа
                if self.app_state.last_active_character:
                    if not self.app_state.last_active_character.is_valid():
                        logging.debug(f"❌ Last active character became invalid, clearing")
                        self.app_state.last_active_character = None
                
                # Получаем активное окно
                user32 = ctypes.windll.user32
                hwnd = user32.GetForegroundWindow()
                
                if hwnd:
                    # Получаем PID окна
                    process_id = wintypes.DWORD()
                    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id))
                    pid = process_id.value
                    
                    # Проверяем что это один из наших персонажей
                    if pid in self.manager.characters:
                        character = self.manager.characters[pid]
                        
                        # Обновляем last_active_character только если валиден
                        if character.is_valid():
                            self.app_state.set_last_active_character(character)
                            logging.debug(f"Active window: {character.char_base.char_name}")
            
            except Exception as e:
                logging.error(f"Error in active window polling: {e}")
            
            # Повторить через 500ms
            self.root.after(500, poll)
        
        # Запустить первый раз
        self.root.after(500, poll)
    
    def _update_party_colors(self):
        """Умное обновление: проверка изменений + обновление цветов"""
        # Проверяем есть ли валидные персонажи
        valid_chars = self.manager.get_all_characters()
        
        if not valid_chars:
            # Нет валидных персонажей - не делаем ничего
            self.root.after(1000, self._update_party_colors)
            return
        
        # Быстрая проверка - нужен ли refresh?
        if self.manager.needs_refresh():
            logging.info("🔄 Auto-refresh triggered by changes")
            self._silent_refresh()
        else:
            # УДАЛЕНО: self.manager.update_group_and_excluded()
            # Просто обновляем цвета (быстро)
            if hasattr(self, 'character_panel'):
                self.character_panel.update_display()
        
        # Повторить через 1 секунду
        self.root.after(1000, self._update_party_colors)

    def _silent_refresh(self):
        """Тихий refresh без мигания"""
        # Обновить список окон в AHK
        self.ahk_manager.refresh_windows()
        
        # УПРОЩЕНО: Лицензия уже проверена при старте, просто используем сохранённый уровень
        # Уровень доступа уже установлен в __init__, здесь ничего не делаем
        
        # Сохраняем старый список персонажей
        old_chars = set(char.pid for char in self.manager.get_all_characters())
        
        # Обновить персонажей
        self.manager.refresh()
        
        # Проверяем изменился ли список валидных персонажей
        new_chars = set(char.pid for char in self.manager.get_all_characters())
        chars_changed = (old_chars != new_chars)
        
        # Обновляем UI ТОЛЬКО если список персонажей изменился
        if chars_changed:
            logging.info(f"🔄 Character list changed: {old_chars} -> {new_chars}")
            self.character_panel.set_characters(self.manager.get_all_characters())
        
        # Обновляем цвета
        self.character_panel.update_display()