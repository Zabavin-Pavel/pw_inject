"""
Персонажи и управление мультибоксом
"""
from characters.character import Character
from characters.manager import MultiboxManager
from characters.behaviors import create_behavior

__all__ = ['Character', 'MultiboxManager', 'create_behavior']