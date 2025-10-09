"""
Игровые структуры
"""
from game_structs.base import GameStruct, GameOriginal, WorldObject
from game_structs.char_base import CharBase
from game_structs.world_manager import WorldManager
from game_structs.loot_item import LootItem
from game_structs.nearby_player import NearbyPlayer
from game_structs.npc import NPC

__all__ = [
    'GameStruct',
    'GameOriginal',
    'WorldObject',
    'CharBase',
    'WorldManager',
    'LootItem',
    'NearbyPlayer',
    'NPC',
]