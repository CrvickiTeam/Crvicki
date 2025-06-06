import pygame
import math
from typing import TYPE_CHECKING, Tuple

from .weapon import Weapon 
from ..projectiles.basic_projectile import BasicProjectile 

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
        super().__init__(owner, game_manager) # game_manager is passed to base

    def activate(self, angle: float, power: float):
        super().activate(angle, power) # Call base to reset projectiles and _is_finished

        # The check below is now mostly redundant if super().activate() is called,
        # as _is_finished would be False and projectiles empty.
        # Keeping it if you have specific logic where it might still be relevant.
        if self._is_finished or self.projectiles: 
            # This path should ideally not be taken if super().activate() was just called.
            # print("BasicCannon: Attempted to activate when already finished or has projectiles (after super call).")
            return

        angle_rad = math.radians(angle)
        velocity_magnitude = power * self.power_to_velocity_scale # Use instance variable
        initial_vx = velocity_magnitude * math.cos(angle_rad)
        initial_vy = -velocity_magnitude * math.sin(angle_rad)

        start_x = self.owner.x 
        start_y = self.owner.y 
        start_pos: Tuple[float, float] = (start_x, start_y)

        projectile = BasicProjectile(
            start_pos, 
            initial_vx, 
            initial_vy, 
            self.owner,
            self.game_manager # <<< PASS self.game_manager
        )
        self.projectiles.append(projectile)
        # self._is_finished is already False due to super().activate()

    # update() is inherited from Weapon
    # draw() is inherited from Weapon
    # is_finished() is inherited from Weapon
