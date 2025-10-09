"""
Окружающий игрок
"""
from game_structs.base import WorldObject

class NearbyPlayer(WorldObject):
    """Окружающий игрок"""
    
    OFFSET_PLAYER_ID = 0x6A8
    
    @property
    def player_id(self):
        value = self._read_int(self.OFFSET_PLAYER_ID)
        return value if value else 0