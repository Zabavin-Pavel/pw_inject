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
INCREASE_MIN = 0
INCREASE_MAX = 0

# LONG/EXIT точки (локация 243)
LONG_LEFT_POINT = (355, -66, 281+INCREASE_MAX)      # <- LONG
LONG_RIGHT_POINT = (270, 330, 288+INCREASE_MAX)     # LONG ->
EXIT_POINT = (-90, 153, 284+INCREASE_MAX)           # EXIT >>

# # QB точки
# _SO_POINT = (-990, 340, 3)     # SO
# SO_POINT = (-800, 480, 3)                   # SO
# _GO_POINT = (1060, -35, 3)     # GO
# GO_POINT = (1200, -129, 3)                  # GO

# ========================================
# ATTACK IDS
# ========================================
GUARD_ID = 111111
BOSS_IDS = [123, 456, 789]

# ========================================
# DUNGEON_POINTS - автоматические точки
# ОБНОВЛЕНО: добавлены count_in_limits
# ========================================
DUNGEON_POINTS = [
    {
        "name": "0 FROST START",
        "trigger": (-210, 282),
        "target": (-210, 183, 256),
        "radius": 40,
        "count_in_limits": False
    },
    {
        "name": "1 FROST GUARD",
        "trigger": (-210, 183),
        "target": (-313, 187, 262),
        "radius": 15,
        "count_in_limits": True
    },
    {
        "name": "2 FROST GUARD", 
        "trigger": (-313, 187),
        "target": (-309, 106, 262),
        "radius": 15,
        "count_in_limits": False
    },
    {
        "name": "3 FROST GUARD", 
        "trigger": (-309, 106),
        "target": (-160, 267, 251),
        "radius": 15,
        "count_in_limits": True
    },
    {
        "name": "4 FROST BOSS 1", 
        "trigger": (-160, 267),
        "target": (-68, 267, 233),
        "radius": 15,
        "count_in_limits": False
    },
    {
        "name": "5 FROST GUARD", 
        "trigger": (-50, 267),
        "target": (-210, -83, 265),
        "radius": 60,
        "count_in_limits": True
    },
    {
        "name": "6 FROST GUARD", 
        "trigger": (-210, -83),
        "target": (-210, -186, 279),
        "radius": 15,
        "count_in_limits": False
    },
    {
        "name": "7 FROST GUARD", 
        "trigger": (-210, -186),
        "target": (-111, -276, 283),
        "radius": 15,
        "count_in_limits": True
    },
    {
        "name": "8 FROST NPCQ 2", 
        "trigger": (-111, -276),
        "target": (-12, -276, 274),
        "radius": 15,
        "count_in_limits": False
    },
    {
        "name": "9 FROST BOSS 2", 
        "trigger": (-12, -276),
        "target": (-25, -352, 274),
        "radius": 15,
        "count_in_limits": False
    },
    {
        "name": "10 FROST NPCQ 3", 
        "trigger": (-25, -352),
        "target": (158, -94, 275),
        "radius": 100,
        "count_in_limits": True
    },
    {
        "name": "11 FROST GUARD", 
        "trigger": (158, -94),
        "target": (265, -146, 279),
        "radius": 60,
        "count_in_limits": True
    },
    {
        "name": "12 FROST BOSS 5", 
        "trigger": (265, -146),
        "target": (340, -10, 281),
        "radius": 15,
        "count_in_limits": True
    },
    {
        "name": "13 FROST GUARD", 
        "trigger": (340, -10),
        "target": (269, 52, 288),
        "radius": 40,
        "count_in_limits": True
    },
    {
        "name": "14 FROST BOSS 6", 
        "trigger": (269, 52),
        "target": (340, 202, 281),
        "radius": 15,
        "count_in_limits": True
    },
    {
        "name": "15 FROST GUARD", 
        "trigger": (340, 202),
        "target": (282, 354, 288),
        "radius": 40,
        "count_in_limits": True
    },
    {
        "name": "16 FROST BOSS 7", 
        "trigger": (282, 354),
        "target": (350, 327, 277),
        "radius": 15,
        "count_in_limits": False
    },
    {
        "name": "17 FROST GUARD", 
        "trigger": (350, 327),
        "target": (32, -117, 275+10),
        "radius": 40,
        "count_in_limits": False
    },
    {
        "name": "18 FROST BOSS 8", 
        "trigger": (32, -117),
        "target": (2, 19, 268),
        "radius": 15,
        "count_in_limits": False
    },
    {
        "name": "19 FROST BOSS 9", 
        "trigger": (2, 19),
        "target": (-90, 153, 284),
        "radius": 60,
        "count_in_limits": False
    },
    {
        "name": "20 FROST BOSS 10", 
        "trigger": (-90, 153),
        "target": (80, 175, 284),
        "radius": 40,
        "count_in_limits": True
    },
    {
        "name": "21 FROST BOSS 11", 
        "trigger": (80, 175),
        "target": (-18, 166, 284),
        "radius": 40,
        "count_in_limits": True
    },
    
    # ========================================
    # QB ТОЧКИ (DEV уровень)
    # ========================================
    {
        "name": "QB SO",
        "trigger": (1433, -1433),
        "target": (-800, 480, 3),
        "radius": 20,
        "count_in_limits": True
    },
    {
        "name": "QB GO START",
        "trigger": (1502, -1366),
        "target": (1200, -129, 3),
        "radius": 20,
        "count_in_limits": True
    },
    {
        "name": "QB GO FINISH",
        "trigger": (583, -538),
        "target": (1200, -129, 3),
        "radius": 20,
        "count_in_limits": True
    },
]