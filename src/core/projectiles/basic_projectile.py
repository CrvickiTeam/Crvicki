import pygame
from .projectile import Projectile # Import the base class

class BasicProjectile(Projectile):
    """
    A simple projectile that moves under gravity and explodes on impact.
    Inherits most functionality from the base Projectile class.
    """
    def __init__(self, start_pos: tuple[float, float], initial_vx: float, initial_vy: float):
        super().__init__(start_pos, initial_vx, initial_vy)
        # No additional initialization needed for this basic version

    # update() is inherited from Projectile
    # draw() is inherited from Projectile
    # is_finished() is inherited from Projectile
