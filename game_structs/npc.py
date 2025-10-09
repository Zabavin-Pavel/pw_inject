"""
NPC и мобы
"""
from game_structs.base import WorldObject

class NPC(WorldObject):
    """NPC или моб"""
    
    # TODO: добавить оффсеты
    
    @property
    def npc_id(self):
        return 0