# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['bot.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets', 'assets'),              # Иконки классов и app icon
        ('ahk/hotkeys.exe', 'ahk'),        # AHK скрипт в папке ahk
    ],
    hiddenimports=[
        'pystray._win32',
        # Явно указываем все модули
        'ahk',
        'ahk.manager',
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

# ВАЖНО: После компиляции структура внутри EXE:
# _internal/
#   ├── assets/
#   │   ├── icon.png
#   │   └── class_icons/
#   └── ahk/
#       └── hotkeys.exe
#
# При первом запуске hotkeys.exe скопируется в:
# C:\Users\USERNAME\AppData\Local\xvocmuk\hotkeys.exe