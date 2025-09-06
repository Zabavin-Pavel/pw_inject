import ctypes
from ctypes import c_float

class Bot:
    def __init__(self, dll_path='pwbot.dll'):
        self.lib = ctypes.CDLL(dll_path)
        self.lib.get_hp.restype = c_float
        self.lib.get_mp.restype = c_float

    def get_hp(self):
        return self.lib.get_hp()

    def get_mp(self):
        return self.lib.get_mp()
