import pygame
import math
import numpy as np # Import numpy here
from typing import TYPE_CHECKING, Dict, Any, Optional, Tuple

# Use TYPE_CHECKING to avoid circular imports for type hints
if TYPE_CHECKING:
    from ..terrain import Terrain
    from ..player import Player

# Constants (can be moved to config or specific projectile types)
PROJECTILE_GRAVITY = 300 # Pixels per second per second
PROJECTILE_SIZE = 5 # Radius for drawing

# Helper function for generating explosion gradient, moved from GameManager
def create_explosion_gradient(x: int, y: int, radius: int, center_strength: int) -> Tuple[int, int, np.ndarray]:
    """
    Generates a circular gradient for terrain destruction.
    Args:
        x: Center x of the explosion in world coordinates.
        y: Center y of the explosion in world coordinates.
        radius: Radius of the explosion.
        center_strength: Strength of destruction at the center.
    Returns:
        A tuple containing:
        - start_x: The top-left x-coordinate for applying the gradient.
        - start_y: The top-left y-coordinate for applying the gradient.
        - gradient: A 2D numpy array representing the destruction strength.
    """
    if radius <= 0: # Handle zero or negative radius
        return x, y, np.array([[]], dtype=np.uint8)
        
    diameter = radius * 2 + 1
    gradient_array = np.zeros((diameter, diameter), dtype=np.uint8)
    # Center of the gradient array itself
    grad_center_x, grad_center_y = radius, radius 

    for i in range(diameter):
        for j in range(diameter):
            dx = i - grad_center_x
            dy = j - grad_center_y
            distance = math.sqrt(dx**2 + dy**2) # Use math.sqrt for clarity
            if distance <= radius:
                strength_val = int(center_strength * max(0, (1 - distance / radius)))
                gradient_array[i, j] = np.clip(strength_val, 0, 255)
    
    # Top-left coordinate in the world for this gradient array
    world_start_x = x - radius
    world_start_y = y - radius
    return world_start_x, world_start_y, gradient_array


class Projectile:
    """Base class for projectiles."""

    def __init__(self, start_pos: tuple[float, float], initial_vx: float, initial_vy: float, owner: 'Player',
                 explosion_radius: int = 30, 
                 max_player_damage: int = 50, 
                 terrain_impact_strength: int = 100):
        """
        Initializes the projectile.

        Args:
            start_pos: The (x, y) starting position (center).
            initial_vx: Initial horizontal velocity.
            initial_vy: Initial vertical velocity.
            owner: The player who fired the projectile.
            explosion_radius: The radius of the explosion upon impact.
            max_player_damage: The maximum damage dealt to players at the center of the explosion.
            terrain_impact_strength: The strength of the impact on terrain.
        """
        self.x, self.y = start_pos
        self.vx = initial_vx
        self.vy = initial_vy
        self.owner = owner # Player who fired this
        self._finished = False # Flag to indicate if the projectile is done
        self._impact_data: Optional[Dict[str, Any]] = None

        # Impact properties - subclasses can override these in their __init__
        self.explosion_radius = explosion_radius
        self.max_player_damage = max_player_damage
        self.terrain_impact_strength = terrain_impact_strength


    def update(self, dt: float, terrain: 'Terrain'): # Removed game_manager from signature
        """
        Updates the projectile's position, checks for collisions.
        If a collision occurs, prepares impact data.

        Args:
            dt: Delta time.
            terrain: The game terrain.
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
        
        collided_or_out_of_bounds = False
        impact_position = (check_x, check_y)

        # 1. Boundary Check (Allow going above screen, y < 0)
        # Finish if outside left/right bounds OR below bottom bound
        if not (0 <= check_x < terrain.width and check_y < terrain.height):
            collided_or_out_of_bounds = True
            # Impact position remains where it went out of bounds
        
        # 2. Terrain Collision Check (simple point check at center)
        # Only check terrain if within vertical bounds (y >= 0) and not already out of bounds
        elif check_y >= 0:
            if terrain.logic_grid[check_x, check_y] != 0: # 0 is TerrainMaterial.EMPTY.value
                collided_or_out_of_bounds = True
                # Impact position is the collision point

        if collided_or_out_of_bounds:
            self._finished = True
            
            # Generate terrain destruction gradient
            # The 'gradient_origin' for Terrain.destroy_terrain is the top-left (start_x, start_y)
            # of the damage_gradient array.
            gradient_start_x, gradient_start_y, terrain_grad_array = create_explosion_gradient(
                int(impact_position[0]), 
                int(impact_position[1]),
                self.explosion_radius,
                self.terrain_impact_strength
            )

            self._impact_data = {
                'position': impact_position, # General center of impact for reference
                'terrain_gradient_offset': (gradient_start_x, gradient_start_y), # This is the 'gradient_origin'
                'terrain_gradient': terrain_grad_array, # The actual numpy array for destruction
                
                # Data for player damage (GameManager will use this)
                'explosion_center': impact_position, 
                'explosion_radius': self.explosion_radius,
                'max_damage': self.max_player_damage,
                'owner': self.owner
            }

    def draw(self, screen: pygame.Surface):
        """
        Draws the projectile.
        """
        if self._finished and not self._impact_data: # Don't draw if finished unless it just impacted
            return 
        pygame.draw.circle(screen, (255, 255, 255), (int(self.x), int(self.y)), PROJECTILE_SIZE)

    def is_finished(self) -> bool:
        """
        Returns True if the projectile has collided or gone out of bounds.
        """
        return self._finished

    def get_impact_data(self) -> Optional[Dict[str, Any]]:
        """
        Returns the data describing the impact, if an impact has occurred.
        Returns None otherwise.
        """
        return self._impact_data