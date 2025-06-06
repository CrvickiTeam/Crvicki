import pygame
import math
from typing import TYPE_CHECKING

from .weapon import Weapon # Import the base class
from ..projectiles.basic_projectile import BasicProjectile # Import the specific projectile

if TYPE_CHECKING:
    from ..player import Player
    from ..game_manager import GameManager

class BasicCannon(Weapon):
    """
    A simple weapon that fires a single BasicProjectile.
    """
    # If BasicCannon needed a *different* scale, you could override it here:
    # POWER_TO_VELOCITY_SCALE = 0.8 # Example override

    def __init__(self, owner: 'Player', game_manager: 'GameManager'):
        super().__init__(owner, game_manager)

    def activate(self, angle: float, power: float):
        """
        Launches a single BasicProjectile.
        """
        if self._is_finished or self.projectiles: 
            print("BasicCannon: Cannot activate, already finished or projectile active.")
            return

        angle_rad = math.radians(angle)
        # Use the POWER_TO_VELOCITY_SCALE from the class (or instance if overridden)
        velocity_magnitude = power * self.POWER_TO_VELOCITY_SCALE 
        initial_vx = velocity_magnitude * math.cos(angle_rad)
        initial_vy = -velocity_magnitude * math.sin(angle_rad)

        start_x = self.owner.x 
        start_y = self.owner.y - (self.owner.rect.height / 2) 
        start_pos = (start_x, start_y)

        projectile = BasicProjectile(start_pos, initial_vx, initial_vy, self.owner)
        self.projectiles.append(projectile)
        self._is_finished = False

    # update() is inherited from Weapon
    # draw() is inherited from Weapon
    # is_finished() is inherited from Weapon
