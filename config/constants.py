"""
Константы и маппинги игры
"""

# Классы персонажей (проверено!)
CLASS_WARRIOR = 0      # Воин
CLASS_MAGE = 1         # Маг
CLASS_DRUID = 3        # Друид
CLASS_TANK = 4         # Танк
CLASS_ASSASSIN = 5     # Ассасин (Син)
CLASS_ARCHER = 6       # Лучник
CLASS_CLERIC = 7       # Жрец (Прист)
CLASS_GUARDIAN = 8     # Страж (Сикер)
CLASS_MYSTIC = 9       # Мистик
CLASS_SHAMAN = 2       # Шаман (предположительно)

# Названия классов для отладки
CLASS_NAMES_DEBUG = {
    CLASS_WARRIOR: "Воин",
    CLASS_MAGE: "Маг",
    CLASS_SHAMAN: "Шаман",
    CLASS_DRUID: "Друид",
    CLASS_TANK: "Танк",
    CLASS_ASSASSIN: "Син",
    CLASS_ARCHER: "Лучник",
    CLASS_CLERIC: "Прист",
    CLASS_GUARDIAN: "Страж",
    CLASS_MYSTIC: "Мистик",
}

# Радиус проверки лута (метры)
LOOT_CHECK_RADIUS = 50

LONG_LEFT_POINT = (-100, 200, 250)    # <- LONG
LONG_RIGHT_POINT = (100, 200, 250)    # LONG ->
EXIT_POINT = (0, 300, 260)            # EXIT >>

# НОВОЕ: Специальные точки для SO/GO
SO_POINT = (-50, -50, 230)            # SO Boss
GO_POINT = (50, 50, 230)              # GO Boss

# Точки подземелья для автоматической телепортации
DUNGEON_POINTS = [
    {
        "name": "0 FROST",
        "trigger": (-210, 282),
        "target": (-210, 183, 255),
        "radius": 30,
        "check_loot": True,
        "mode": "party"  # party или solo
    },
    {
        "name": "1 GUARD",
        "trigger": (-210, 183),
        "target": (-313, 187, 261),
        "radius": 30,
        "check_loot": True,
        "mode": "party"  # party или solo
    },
    {
        "name": "2 GUARD", 
        "trigger": (-313, 187),
        "target": (-309, 106, 261),
        "radius": 30,
        "check_loot": True,
        "mode": "party"
    },
    {
        "name": "3 GUARD", 
        "trigger": (-309, 106),
        "target": (-160, 267, 250),
        "radius": 30,
        "check_loot": True,
        "mode": "party"
    },
    {
        "name": "4 BOSS 1", 
        "trigger": (-160, 267),
        "target": (-50, 267, 232),
        "radius": 30,
        "check_loot": True,
        "mode": "party"
    },
    {
        "name": "5 GUARD", 
        "trigger": (-50, 267),
        "target": (-210, -83, 264),
        "radius": 50,
        "check_loot": True,
        "mode": "party"
    },
    {
        "name": "6 GUARD", 
        "trigger": (-210, -83),
        "target": (-210, -186, 278),
        "radius": 50,
        "check_loot": True,
        "mode": "party"
    },
    {
        "name": "7 GUARD", 
        "trigger": (-210, -186),
        "target": (-111, -276, 282),
        "radius": 50,
        "check_loot": True,
        "mode": "party"
    },
    {
        "name": "8 NPCQ 2", 
        "trigger": (-111, -276),
        "target": (-12, -276, 273),
        "radius": 50,
        "check_loot": True,
        "mode": "party"
    },
    {
        "name": "9 NPCQ 3", 
        "trigger": (-12, -276),
        "target": (158, -94, 274),
        "radius": 50,
        "check_loot": True,
        "mode": "party"
    },
    {
        "name": "10 GUARD", 
        "trigger": (158, -94),
        "target": (265, -146, 278),
        "radius": 50,
        "check_loot": True,
        "mode": "party"
    },
    {
        "name": "11 GUARD 4", 
        "trigger": (265, -146),
        "target": (340, -10, 280),
        "radius": 50,
        "check_loot": True,
        "mode": "party"
    },
    {
        "name": "12 BOSS 5", 
        "trigger": (340, -10),
        "target": (269, 52, 287),
        "radius": 50,
        "check_loot": True,
        "mode": "party"
    },
    {
        "name": "13 BOSS 6", 
        "trigger": (269, 52),
        "target": (340, 202, 280),
        "radius": 50,
        "check_loot": True,
        "mode": "party"
    },
    {
        "name": "14 GUARD", 
        "trigger": (340, 202),
        "target": (282, 354, 287),
        "radius": 50,
        "check_loot": True,
        "mode": "party"
    },
    {
        "name": "15 BOSS 7", 
        "trigger": (282, 354),
        "target": (367, 327, 276),
        "radius": 50,
        "check_loot": True,
        "mode": "party"
    },
    {
        "name": "16 GUARD", 
        "trigger": (367, 327),
        "target": (32, -117, 274),
        "radius": 50,
        "check_loot": True,
        "mode": "party"
    },
    {
        "name": "17 BOSS 8", 
        "trigger": (32, -117),
        "target": (2, 19, 267),
        "radius": 50,
        "check_loot": True,
        "mode": "party"
    },
    {
        "name": "18 BOSS 9", 
        "trigger": (2, 19),
        "target": (-90, 153, 283),
        "radius": 50,
        "check_loot": True,
        "mode": "party"
    },
]