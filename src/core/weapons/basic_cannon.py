import pygame
import math
from typing import TYPE_CHECKING

from .weapon import Weapon # Import the base class
from ..projectiles.basic_projectile import BasicProjectile # Import the specific projectile

if TYPE_CHECKING:
    from ..player import Player
    from ..game_manager import GameManager

# Power scaling factor (adjust as needed)
# Maps the player's aim_power (e.g., 0-100) to initial velocity magnitude
POWER_TO_VELOCITY_SCALE = 5

class BasicCannon(Weapon):
    """
    A simple weapon that fires a single BasicProjectile.
    """
    def __init__(self, owner: 'Player', game_manager: 'GameManager'):
        super().__init__(owner, game_manager)

    def activate(self, angle: float, power: float):
        """
        Launches a single BasicProjectile.
        """
        if self._is_finished: # Prevent re-activation
            return

        # Calculate initial velocity components
        angle_rad = math.radians(angle)
        # Scale power to a suitable velocity magnitude
        velocity_magnitude = power * POWER_TO_VELOCITY_SCALE
        initial_vx = velocity_magnitude * math.cos(angle_rad)
        initial_vy = -velocity_magnitude * math.sin(angle_rad) # Negative because pygame y-axis is inverted

        # Determine starting position (e.g., player's center)
        # Could be offset later based on player sprite/weapon position
        start_pos = (self.owner.x, self.owner.y)

        # Create the projectile
        projectile = BasicProjectile(start_pos, initial_vx, initial_vy)

        # Add it to the list managed by this weapon instance
        self.projectiles.append(projectile)

    # update() is inherited from Weapon
    # draw() is inherited from Weapon
    # is_finished() is inherited from Weapon
