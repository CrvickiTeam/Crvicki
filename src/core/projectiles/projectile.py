import pygame
import math
from typing import TYPE_CHECKING

# Use TYPE_CHECKING to avoid circular imports for type hints
if TYPE_CHECKING:
    from ..terrain import Terrain
    from ..game_manager import GameManager

# Constants (can be moved to config or specific projectile types)
PROJECTILE_GRAVITY = 300 # Pixels per second per second
PROJECTILE_SIZE = 5 # Radius for drawing

class Projectile:
    """Base class for projectiles."""

    def __init__(self, start_pos: tuple[float, float], initial_vx: float, initial_vy: float):
        """
        Initializes the projectile.

        Args:
            start_pos: The (x, y) starting position (center).
            initial_vx: Initial horizontal velocity.
            initial_vy: Initial vertical velocity.
        """
        self.x, self.y = start_pos
        self.vx = initial_vx
        self.vy = initial_vy
        self._finished = False # Flag to indicate if the projectile is done

    def update(self, dt: float, terrain: 'Terrain', game_manager: 'GameManager'):
        """
        Updates the projectile's position, checks for collisions.

        Args:
            dt: Delta time.
            terrain: The game terrain.
            game_manager: Reference to the game manager to trigger effects (e.g., explosions).
        """
        if self._finished:
            return

        # Apply gravity
        self.vy += PROJECTILE_GRAVITY * dt

        # Update position
        self.x += self.vx * dt
        self.y += self.vy * dt

        # --- Collision Checks ---
        check_x = int(self.x)
        check_y = int(self.y)

        # 1. Boundary Check (Allow going above screen, y < 0)
        # Finish if outside left/right bounds OR below bottom bound
        if not (0 <= check_x < terrain.width and check_y < terrain.height):
            self._finished = True
            # Optional: Explode even if out of bounds? Or just disappear?
            # game_manager.explode(check_x, check_y) # Example: Explode where it went out
            return # Stop further processing if out of bounds

        # 2. Terrain Collision Check (simple point check at center)
        # Only check terrain if within vertical bounds (y >= 0)
        if check_y >= 0:
            # More robust checks might use the projectile's rect or shape
            # Assuming terrain.logic_grid uses [x, y] indexing
            if terrain.logic_grid[check_x, check_y] != 0: # 0 is TerrainMaterial.EMPTY.value
                self._finished = True
                # Trigger explosion via GameManager
                game_manager.explode(check_x, check_y)
                return # Stop further processing after collision

    def draw(self, screen: pygame.Surface):
        """
        Draws the projectile.

        Args:
            screen: The pygame surface to draw on.
        """
        if self._finished:
            return
        # Draw a simple circle (even if it's above the screen, pygame handles clipping)
        pygame.draw.circle(screen, (255, 255, 255), (int(self.x), int(self.y)), PROJECTILE_SIZE)

    def is_finished(self) -> bool:
        """
        Returns True if the projectile has collided or gone out of bounds (excluding above screen).
        """
        return self._finished