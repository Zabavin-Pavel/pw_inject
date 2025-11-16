# -*- mode: python ; coding: utf-8 -*-
import shutil
from pathlib import Path

# ========================================
# ПОИСК AutoHotkey.exe из venv
# ========================================
ahk_exe_path = shutil.which('AutoHotkey.exe')
if not ahk_exe_path:
    raise FileNotFoundError('AutoHotkey.exe не найден. Установите AHK: pip install ahk')

print(f"✅ Found AutoHotkey.exe: {ahk_exe_path}")

# ========================================
# АНАЛИЗ
# ========================================
block_cipher = None

a = Analysis(
    ['xvocmuk.py'],
    pathex=[],
    binaries=[
        # НОВОЕ: Упаковываем AutoHotkey.exe из venv
        (ahk_exe_path, '.'),
    ],
    datas=[
        # Иконки классов и app icon
        ('assets', 'assets'),
        
        # ОБНОВЛЕНО: Только settings.ini (БЕЗ hotkeys.exe!)
        ('ahk_local/settings.ini', 'ahk_local'),  # Было: ahk/settings.ini
    ],
    hiddenimports=[
        'pystray._win32',
        
        # НОВОЕ: AHK библиотека (все модули)
        'ahk',
        'ahk.directives',
        'ahk._sync',
        'ahk._sync.engine',
        'ahk._sync.transport',
        'ahk._hotkey',
        'ahk._utils',
        
        # Остальные модули приложения
        'ahk_local.manager',
        'actions',
        'actions.toggle_actions',
        'actions.try_actions',
        'actions.pro_actions',
        'actions.dev_actions',
        'characters',
        'characters.character',
        'characters.behaviors',
        'characters.multibox_manager',
        'game',
        'game.memory',
        'game.structs',
        'game.offsets',
        'game.win32_api',
        'config',
        'config.constants',
        'config.settings',
        'core',
        'core.app_state',
        'core.action_manager',
        'core.hotkey_manager',
        'core.license',
        'core.license_manager',
        'core.keygen',
        'gui',
        'gui.main_window',
        'gui.character_panel',
        'gui.hotkey_panel',
        'gui.styles',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# ========================================
# СБОРКА
# ========================================
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='xvocmuk',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,                          # Без консоли (GUI приложение)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.png'
)

# ========================================
# ВАЖНО: После компиляции структура:
# ========================================
# xvocmuk.exe (в корне)
# _internal/
#   ├── AutoHotkey.exe        ← из venv!
#   ├── assets/
#   │   ├── icon.png
#   │   └── class_icons/
#   └── ahk/
#       └── settings.ini        ← шаблон
#
# При первом запуске:
# - settings.ini скопируется в AppData/Local/xvocmuk/ (только если отсутствует)