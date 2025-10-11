"""
Предмет на земле
"""
from game_structs.base import WorldObject

class LootItem(WorldObject):
    """Предмет на земле"""
    
    OFFSET_ITEM_ID = 0x140
    
    @property
    def item_id(self):
        value = self._read_int(self.OFFSET_ITEM_ID)
        return value if value else 0