import pygame
from typing import TYPE_CHECKING
from .projectile import Projectile # Import the base class

if TYPE_CHECKING:
    from ..player import Player

class BasicProjectile(Projectile):
    """
    A simple projectile that moves under gravity and causes an impact.
    Inherits most functionality from the base Projectile class.
    Defines specific parameters for its impact.
    """
    def __init__(self, start_pos: tuple[float, float], initial_vx: float, initial_vy: float, owner: 'Player'):
        # Define specific parameters for a BasicProjectile's impact
        explosion_radius = 35  # Example value
        max_player_damage = 40 # Example value
        terrain_impact_strength = 120 # Example value for terrain deformation

        super().__init__(start_pos, initial_vx, initial_vy, owner,
                         explosion_radius=explosion_radius,
                         max_player_damage=max_player_damage,
                         terrain_impact_strength=terrain_impact_strength)

    # update() is inherited from Projectile
    # draw() is inherited from Projectile
    # is_finished() is inherited from Projectile
    # get_impact_data() is inherited from Projectile
