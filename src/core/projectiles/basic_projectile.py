import pygame # Keep if BasicProjectile might need it directly later
from typing import TYPE_CHECKING
from .projectile import Projectile # Import the base class

if TYPE_CHECKING:
    from ..player import Player
    from ..game_manager import GameManager

class BasicProjectile(Projectile):
    """
    A simple projectile that moves under gravity and causes an impact.
    Inherits most functionality from the base Projectile class.
    Defines specific parameters for its impact.
    """
    def __init__(self, start_pos: tuple[float, float], initial_vx: float, initial_vy: float, 
                 owner: 'Player',
                 game_manager: 'GameManager',
                 explosion_radius: int = 30, # Default for BasicProjectile if not specified by weapon
                 center_damage: int = 50):   # Default for BasicProjectile if not specified by weapon
        
        # Pass game_manager, explosion_radius, and center_damage to the superclass constructor.
        # Projectile.__init__ will use center_damage to set its gradient_center_strength.
        super().__init__(start_pos, initial_vx, initial_vy, owner,
                         game_manager, 
                         explosion_radius=explosion_radius,
                         center_damage=center_damage)
        # No need to pass terrain_impact_strength to super, as Projectile doesn't use it in __init__.
        # The gradient_center_strength (derived from center_damage) is what Projectile uses for create_explosion_gradient.

    # update() is inherited from Projectile
    # draw() is inherited from Projectile
    # is_finished() is inherited from Projectile
    # get_impact_data() is inherited from Projectile
