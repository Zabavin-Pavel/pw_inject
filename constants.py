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

# Точки подземелья для автоматической телепортации
DUNGEON_POINTS = [
    {
        "name": "SO Boss",
        "trigger": (1430, -1430),
        "target": (-800, 480, 2),
        "radius": 50,
        "check_loot": True,
        "mode": "party"  # party или solo
    },
    {
        "name": "GO Boss", 
        "trigger": (-840, 440),
        "target": (1200, -129, 2),
        "radius": 50,
        "check_loot": True,
        "mode": "party"
    },
    {
        "name": "test point", 
        "trigger": (474, -2789),
        "target": (410, -2740, 700),
        "radius": 50,
        "check_loot": False,
        "mode": "solo"
    },
]