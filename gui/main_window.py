"""
Главное окно приложения
"""
import tkinter as tk
from PIL import Image, ImageTk
import logging
import sys
import pystray
from pystray import MenuItem as item
import threading

from gui.styles import *
from gui.character_panel import CharacterPanel
from gui.hotkey_panel import HotkeyPanel
from core import AppState, ActionManager, HotkeyManager, LicenseManager
from license_manager import LicenseConfig
from keygen import PERMISSION_NONE, PERMISSION_TRY, PERMISSION_PRO, PERMISSION_DEV
from ahk_manager import AHKManager

class MainWindow:
    """Главное окно - координатор"""
    
    def __init__(self, multibox_manager, settings_manager):
        self.manager = multibox_manager
        self.settings_manager = settings_manager
        
        # НОВОЕ: Менеджер лицензий (license.ini)
        self.license_config = LicenseConfig()
        
        # НОВОЕ: Предыдущий уровень доступа (для оптимизации UI)
        self.prev_permission_level = PERMISSION_NONE
        
        # Состояние приложения
        self.app_state = AppState()
        
        # Менеджеры
        self.action_manager = ActionManager(self.app_state)
        self.hotkey_manager = HotkeyManager(
            self.action_manager,
            on_hotkey_executed=self._on_hotkey_flash
        )
        
        # ВАЖНО: Создаём AHK менеджер ДО регистрации действий
        from ahk_manager import AHKManager
        self.ahk_manager = AHKManager()
        
        # Регистрируем действия (ПОСЛЕ создания ahk_manager!)
        self._register_actions()
        
        # Создать UI
        self._create_ui()
        
        # Загрузить хоткеи из настроек
        self._load_hotkeys()
        
        # Создать tray icon
        self._create_tray_icon()
        
        # Применить topmost из настроек
        self.is_topmost = self.settings_manager.is_topmost()
        self.root.attributes('-topmost', self.is_topmost)

        self.on_refresh()  # Задержка 500ms для инициализации UI
    
    def _register_actions(self):
        """Зарегистрировать все действия с уровнями доступа"""
        # Toggle действия с иконками (без хоткеев)
        self.action_manager.register(
            'follow',
            label='Follow',
            type='toggle',
            callback=self.toggle_follow,
            icon='👣',
            has_hotkey=False,
            required_permission=PERMISSION_TRY  # TRY
        )
        
        self.action_manager.register(
            'attack',
            label='Attack',
            type='toggle',
            callback=self.toggle_attack,
            icon='⚔️',
            has_hotkey=False,
            required_permission=PERMISSION_PRO  # PRO
        )
        
        self.action_manager.register(
            'teleport',
            label='Teleport',
            type='toggle',
            callback=self.toggle_teleport,
            icon='🌀',
            has_hotkey=False,
            required_permission=PERMISSION_DEV  # DEV
        )
        
        # Quick действия с хоткеями (без иконок)
        self.action_manager.register(
            'teleport_to_target',
            label='Teleport to Target',
            type='quick',
            callback=self.action_teleport_to_target,
            has_hotkey=True,
            required_permission=PERMISSION_PRO  # PRO
        )
        
        self.action_manager.register(
            'show_all',
            label='Show All Characters',
            type='quick',
            callback=self.action_show_all,
            has_hotkey=True,
            required_permission=PERMISSION_TRY  # TRY
        )
        
        self.action_manager.register(
            'show_active',
            label='Show Active Characters',
            type='quick',
            callback=self.action_show_active,
            has_hotkey=True,
            required_permission=PERMISSION_TRY  # TRY
        )
        
        self.action_manager.register(
            'show_loot',
            label='Show Nearby Loot',
            type='quick',
            callback=self.action_show_loot,
            has_hotkey=True,
            required_permission=PERMISSION_PRO  # PRO
        )
        
        self.action_manager.register(
            'show_players',
            label='Show Nearby Players',
            type='quick',
            callback=self.action_show_players,
            has_hotkey=True,
            required_permission=PERMISSION_PRO  # PRO
        )
        
        self.action_manager.register(
            'show_npcs',
            label='Show Nearby NPC',
            type='quick',
            callback=self.action_show_npcs,
            has_hotkey=True,
            required_permission=PERMISSION_DEV  # DEV
        )
    
        # AHK экшены
        self.action_manager.register(
            'ahk_click_mouse',
            label='AHK: Click at Mouse',
            type='quick',
            callback=self.ahk_manager.click_at_mouse,
            has_hotkey=True,
            required_permission=PERMISSION_TRY  # TRY
        )

        self.action_manager.register(
            'ahk_press_space',
            label='AHK: Press Space',
            type='quick',
            callback=lambda: self.ahk_manager.send_key("Space"),
            has_hotkey=True,
            required_permission=PERMISSION_TRY  # TRY
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
        # ПОРЯДОК: Refresh, Pin, Minimize, Close

        # Кнопка Close (ЧЕТВЁРТАЯ)
        self.close_btn = tk.Label(
            self.title_bar,
            text="✕",
            font=("Segoe UI", 15, "bold"),  # Жирнее
            bg=COLOR_BG,
            fg=COLOR_TEXT,
            cursor="hand2",
            width=2,
            height=1,
            anchor="center"
        )
        self.close_btn.pack(side=tk.RIGHT, padx=(0, 10))  # Отступ от края
        self.close_btn.bind("<Button-1>", lambda e: self.on_close())
        self.close_btn.bind("<Enter>", lambda e: self.close_btn.configure(fg=COLOR_ACCENT))
        self.close_btn.bind("<Leave>", lambda e: self.close_btn.configure(fg=COLOR_TEXT))

        # Кнопка Minimize (ТРЕТЬЯ)
        self.minimize_btn = tk.Label(
            self.title_bar,
            text="−",
            font=("Segoe UI", 15, "bold"),  # Жирнее
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

        # Кнопка Pin (ВТОРАЯ)
        self.pin_btn = tk.Label(
            self.title_bar,
            text="📌",
            font=("Segoe UI", 13),  # Увеличен размер
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

        # Кнопка Refresh (ПЕРВАЯ)
        self.refresh_btn = tk.Label(
            self.title_bar,
            text="⟳",
            font=("Segoe UI", 15, "bold"),  # Жирнее и крупнее
            bg=COLOR_BG,
            fg=COLOR_TEXT,
            cursor="hand2",
            width=3,
            height=1,
            anchor="center"
        )
        self.refresh_btn.pack(side=tk.RIGHT, padx=0)
        self.refresh_btn.bind("<Button-1>", lambda e: self.on_refresh())
        self.refresh_btn.bind("<Enter>", lambda e: self.refresh_btn.configure(fg=COLOR_ACCENT))
        self.refresh_btn.bind("<Leave>", lambda e: self.refresh_btn.configure(fg=COLOR_TEXT))
        
        # Drag window - привязка к title bar
        self.title_bar.bind("<Button-1>", self._start_drag)
        self.title_bar.bind("<B1-Motion>", self._do_drag)
        title_label.bind("<Button-1>", self._start_drag)
        title_label.bind("<B1-Motion>", self._do_drag)
        
        # === MAIN CONTENT ===
        content_frame = tk.Frame(self.root, bg=COLOR_BG)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=0)
        
        # Левая панель: персонажи (ФИКСИРОВАННАЯ ШИРИНА + РАМКА)
        left_container = tk.Frame(
            content_frame, 
            bg=COLOR_BG, 
            width=CHARACTERS_PANEL_WIDTH,
            highlightthickness=1,
            highlightbackground=COLOR_BORDER
        )
        left_container.pack(side=tk.LEFT, fill=tk.Y, expand=False, padx=(0, 10))
        left_container.pack_propagate(False)
        
        self.character_panel = CharacterPanel(
            left_container,
            self.app_state,
            on_character_selected=self.on_character_selected,
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
    
    def _flash_refresh_button(self):
        """Мигнуть кнопкой Refresh"""
        self.refresh_btn.configure(fg=COLOR_ACCENT)
        self.root.after(200, lambda: self.refresh_btn.configure(fg=COLOR_TEXT))
    
    def on_refresh(self):
        """Обработчик кнопки Refresh - С ВЕРИФИКАЦИЕЙ ПРИ КАЖДОМ ВЫЗОВЕ"""
        # Мигнуть кнопкой
        self._flash_refresh_button()
        
        # Обновить список окон в AHK
        self.ahk_manager.refresh_windows()
        
        # === ШАГ 1: ВЕРИФИКАЦИЯ (КАЖДЫЙ РАЗ!) ===
        success, permission_level = LicenseManager.verify_best_license(self.license_config)
        
        # Обновляем состояние приложения
        self.verified = success
        self.app_state.permission_level = permission_level
        
        logging.info(f"🔐 Verification: {success}, Permission: {permission_level}")
        
        # === ОПТИМИЗАЦИЯ: Обновлять UI только если уровень изменился ===
        permission_changed = (permission_level != self.prev_permission_level)
        
        if permission_changed:
            logging.info(f"🔄 Permission changed: {self.prev_permission_level} → {permission_level}")
            self.prev_permission_level = permission_level
            
            # Пересоздать hotkey panel (показать/скрыть экшены)
            self._rebuild_hotkey_panel()
        
        # === ШАГ 2: ЗАГРУЗКА ПЕРСОНАЖЕЙ (если верификация OK) ===
        if self.verified and permission_level != PERMISSION_NONE:
            # Обновляем список персонажей
            self.manager.refresh_characters()
            characters = self.manager.get_valid_characters()
            
            # Отображаем персонажей
            self.character_panel.set_characters(characters)
        else:
            # Нет доступа - очистить всё
            self.character_panel.set_characters([])
            
            logging.warning("❌ No valid license - access denied")
    
    def _rebuild_hotkey_panel(self):
        """Пересоздать hotkey panel (для обновления видимости экшенов)"""
        # Удаляем старый hotkey_panel
        self.hotkey_panel.destroy()
        
        # Создаём новый hotkey_panel
        self.hotkey_panel = HotkeyPanel(
            self.right_container,
            self.app_state,
            self.action_manager,
            self.hotkey_manager,
            self.settings_manager,
            on_action_executed=self.on_action_executed
        )
        self.hotkey_panel.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Обновить отображение хоткеев
        self.root.after(100, lambda: self.hotkey_panel.update_hotkey_display())

    def on_character_selected(self, character):
        """Обработчик клика по никнейму персонажа - toggle выбора"""
        # Если этот персонаж уже выбран - снять выбор
        if self.app_state.selected_character == character:
            self.app_state.select_character(None)
        else:
            # Иначе - выбрать его
            self.app_state.select_character(character)
        
        # Обновить отображение
        self.character_panel.update_display()
    
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
    
    def _start_action_loop(self, action_id: str, message: str):
        """Запустить циклический вывод сообщения (раз в секунду)"""
        def loop():
            if self.app_state.is_action_active(action_id):
                print(message)
                # TODO: Здесь будет работа с памятью и логика бота
                self.action_timers[action_id] = self.root.after(1000, loop)
        
        loop()
    
    def _stop_action_loop(self, action_id: str):
        """Остановить циклический вывод"""
        if action_id in self.action_timers:
            timer_id = self.action_timers[action_id]
            if timer_id:
                try:
                    self.root.after_cancel(timer_id)
                except:
                    pass
            self.action_timers[action_id] = None
    
    def toggle_follow(self):
        """Toggle: Следование"""
        is_active = self.app_state.is_action_active('follow')
        
        if is_active:
            print("Follow: STARTED")
            self._start_action_loop('follow', "СЛЕДУЮ")
        else:
            print("Follow: STOPPED")
            self._stop_action_loop('follow')
        
        self.hotkey_panel.update_display()
    
    def toggle_attack(self):
        """Toggle: Атака"""
        is_active = self.app_state.is_action_active('attack')
        
        if is_active:
            print("Attack: STARTED")
            self._start_action_loop('attack', "АТАКУЮ")
        else:
            print("Attack: STOPPED")
            self._stop_action_loop('attack')
        
        self.hotkey_panel.update_display()
    
    def toggle_teleport(self):
        """Toggle: Телепорт"""
        is_active = self.app_state.is_action_active('teleport')
        
        if is_active:
            print("Teleport: STARTED")
            self._start_action_loop('teleport', "ТЕЛЕПОРТИРУЮСЬ")
        else:
            print("Teleport: STOPPED")
            self._stop_action_loop('teleport')
        
        self.hotkey_panel.update_display()
    
    def action_teleport_to_target(self):
        """Action: Телепортировать к таргету"""
        selected = self.app_state.selected_character
        
        if not selected:
            print("\n[Teleport to Target] Нет выбранного персонажа")
            return
        
        success = self.manager.action_teleport_to_target(selected)
        
        if not success:
            char_name = selected.char_base.char_name
            print(f"[Teleport to Target] {char_name}: Неудача (нет таргета или ошибка записи)\n")

    def action_show_all(self):
        """Action: Показать всех персонажей"""
        characters = self.manager.get_all_characters()
        
        print("\n=== Все персонажи ===")
        for char in characters:
            name = char.char_base.char_name
            char_id = char.char_base.char_id
            char_class = char.char_base.char_class
            print(f"  {name} (ID:{char_id}, Class:{char_class})")
        print(f"Всего: {len(characters)}\n")
    
    def action_show_active(self):
        """Action: Показать активных персонажей"""
        active_chars = list(self.app_state.active_characters)
        
        print("\n=== Активные персонажи ===")
        for char in active_chars:
            name = char.char_base.char_name
            print(f"  {name}")
        print(f"Всего активных: {len(active_chars)}\n")
    
    def action_show_loot(self):
        """Action: Показать лут вокруг"""
        selected = self.app_state.selected_character
        
        if selected:
            loot_ids = self.manager.get_nearby_loot(selected)
        else:
            loot_ids = self.manager.get_nearby_loot()
        
        print("\n=== Лут вокруг ===")
        for loot_id in loot_ids:
            print(f"  Лут ID: {loot_id}")
        print(f"Всего предметов: {len(loot_ids)}\n")
    
    def action_show_players(self):
        """Action: Показать игроков вокруг"""
        selected = self.app_state.selected_character
        
        if selected:
            player_ids = self.manager.get_nearby_players(selected)
        else:
            player_ids = self.manager.get_nearby_players()
        
        print("\n=== Окружающие игроки ===")
        for player_id in player_ids:
            print(f"  Игрок ID: {player_id}")
        print(f"Всего игроков: {len(player_ids)}\n")
    
    def action_show_npcs(self):
        """Action: Показать NPC вокруг"""
        npc_ids = self.manager.get_nearby_npcs()
        
        print("\n=== Окружающие NPC ===")
        for npc_id in npc_ids:
            print(f"  NPC ID: {npc_id}")
        print(f"Всего NPC: {len(npc_ids)}\n")
    
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