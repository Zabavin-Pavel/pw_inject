"""
Поведения классов персонажей
"""
from abc import ABC, abstractmethod
from constants import *

class BaseBehavior(ABC):
    """Базовое поведение для всех классов"""
    
    def __init__(self, character):
        self.char = character
    
    def tick(self):
        """Основной цикл поведения"""
        self.on_tick()
    
    def follow_leader(self, leader_position):
        """Следовать за лидером"""
        pass
    
    @abstractmethod
    def on_tick(self):
        """Специфичное поведение класса"""
        pass
    
    @abstractmethod
    def on_combat(self, target):
        """Поведение в бою"""
        pass


class WarriorBehavior(BaseBehavior):
    """Воин (0)"""
    def on_tick(self):
        pass
    def on_combat(self, target):
        pass


class MageBehavior(BaseBehavior):
    """Маг (1) - DD"""
    def on_tick(self):
        pass
    def on_combat(self, target):
        pass


class ShamanBehavior(BaseBehavior):
    """Шаман (2)"""
    def on_tick(self):
        pass
    def on_combat(self, target):
        pass


class DruidBehavior(BaseBehavior):
    """Друид (3)"""
    def on_tick(self):
        pass
    def on_combat(self, target):
        pass


class TankBehavior(BaseBehavior):
    """Танк (4)"""
    def on_tick(self):
        pass
    def on_combat(self, target):
        pass


class AssassinBehavior(BaseBehavior):
    """Син (5)"""
    def on_tick(self):
        pass
    def on_combat(self, target):
        pass


class ArcherBehavior(BaseBehavior):
    """Лучник (6)"""
    def on_tick(self):
        pass
    def on_combat(self, target):
        pass


class ClericBehavior(BaseBehavior):
    """Прист (7) - хил"""
    def on_tick(self):
        pass
    def on_combat(self, target):
        pass


class GuardianBehavior(BaseBehavior):
    """Страж (8)"""
    def on_tick(self):
        pass
    def on_combat(self, target):
        pass


class MysticBehavior(BaseBehavior):
    """Мистик (9)"""
    def on_tick(self):
        pass
    def on_combat(self, target):
        pass


# Маппинг: класс -> поведение
BEHAVIOR_MAP = {
    CLASS_WARRIOR: WarriorBehavior,
    CLASS_MAGE: MageBehavior,
    CLASS_SHAMAN: ShamanBehavior,
    CLASS_DRUID: DruidBehavior,
    CLASS_TANK: TankBehavior,
    CLASS_ASSASSIN: AssassinBehavior,
    CLASS_ARCHER: ArcherBehavior,
    CLASS_CLERIC: ClericBehavior,
    CLASS_GUARDIAN: GuardianBehavior,
    CLASS_MYSTIC: MysticBehavior,
}


def create_behavior(character):
    """
    Создать поведение для персонажа на основе класса
    Возвращает None если класс неизвестен
    """
    char_class = character.char_base.char_class
    if char_class is None:
        return None
    
    behavior_class = BEHAVIOR_MAP.get(char_class)
    if behavior_class:
        return behavior_class(character)
    
    return None