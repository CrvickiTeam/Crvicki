import pygame
import math
import numpy as np 
from typing import TYPE_CHECKING, Dict, Any, Optional, Tuple

if TYPE_CHECKING:
    from ..terrain import Terrain
    from ..player import Player
    from ..game_manager import GameManager # For type hinting game_manager

# Helper function for generating explosion gradient
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
    if radius < 0: # Handle negative radius as an error or minimal case
        radius = 0

    if radius == 0: # Point impact
        gradient_array = np.array([[center_strength]], dtype=np.uint8)
        return x, y, gradient_array
        
    diameter = radius * 2 + 1
    gradient_array = np.zeros((diameter, diameter), dtype=np.uint8)
    grad_center_x, grad_center_y = radius, radius 

    for i in range(diameter):
        for j in range(diameter):
            dx = i - grad_center_x
            dy = j - grad_center_y
            distance = math.sqrt(dx**2 + dy**2) 
            if distance <= radius: # Ensure we are within the circle
                strength_val = int(center_strength * max(0, (1 - distance / radius)))
                gradient_array[i, j] = np.clip(strength_val, 0, 255)
    
    world_start_x = x - radius
    world_start_y = y - radius
    return world_start_x, world_start_y, gradient_array


class Projectile:
    """Base class for projectiles."""

    def __init__(self, start_pos: tuple[float, float], initial_vx: float, initial_vy: float, owner: 'Player',
                 game_manager: 'GameManager', 
                 explosion_radius: int = 30, 
                 center_damage: int = 50):
        """
        Initializes the projectile.

        Args:
            start_pos: The (x, y) starting position (center).
            initial_vx: Initial horizontal velocity.
            initial_vy: Initial vertical velocity.
            owner: The player who fired the projectile.
            game_manager: The GameManager instance to access config.
            explosion_radius: The radius of the explosion upon impact.
            max_player_damage: The maximum damage dealt to players at the center of the explosion.
            terrain_impact_strength: The strength of the impact on terrain.
        """
        self.x, self.y = start_pos
        self.vx = initial_vx
        self.vy = initial_vy
        self.owner = owner # Player who fired this
        self.game_manager = game_manager 
        self._finished = False # Flag to indicate if the projectile is done
        self._impact_data: Optional[Dict[str, Any]] = None

        # Load defaults from config via game_manager
        proj_defaults_cfg = game_manager.config.get("game", {}).get("projectiles", {}).get("defaults", {})

        self.gravity: float = float(proj_defaults_cfg.get("gravity", 300.0)) # Default if not in config
        self.draw_size_radius: int = int(proj_defaults_cfg.get("draw_size_radius", 5)) # Default if not in config

        # Impact properties - these are direct parameters, not from config in this version
        self.explosion_radius = explosion_radius
        # We'll use max_player_damage as the 'center_strength' for the explosion gradient
        # that affects both terrain and players.
        self.max_player_damage = center_damage 
        # terrain_impact_strength could be used if you want different strengths for terrain vs player,
        # but if one gradient is used for both, max_player_damage is a good candidate for its peak.
        # For simplicity, let's assume the gradient's center_strength is primarily driven by max_player_damage.
        # If terrain needs a different value, the weapon config should specify what to pass to create_explosion_gradient.
        # For now, let's assume the weapon will tell the projectile what 'center_strength' to use for its gradient.
        # So, the projectile constructor might take a 'gradient_center_strength' parameter.
        # Or, we use self.max_player_damage as the primary strength for the gradient.
        self.gradient_center_strength = center_damage # This will be the peak of the explosion.


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

        self.vy += self.gravity * dt # Use instance attribute self.gravity

        self.x += self.vx * dt
        self.y += self.vy * dt

        proj_point = (int(self.x), int(self.y))
        
        collided_this_frame = False
        impact_position: Tuple[int, int] = proj_point
        
        # 1. Check for Player Collision
        for player in self.game_manager.players:
            if player is not self.owner and player.alive:
                if player.rect.collidepoint(proj_point):
                    collided_this_frame = True
                    # impact_position is already proj_point
                    break 

        # 2. If no player collision, check for Terrain or Out of Bounds
        if not collided_this_frame:
            check_x, check_y = proj_point
            if not (0 <= check_x < terrain.width and check_y < terrain.height):
                collided_this_frame = True
            elif check_y >= 0:
                if terrain.logic_grid[min(check_x, terrain.width-1), min(check_y, terrain.height-1)] != 0: 
                    collided_this_frame = True
        
        if collided_this_frame:
            self._finished = True
            
            # The gradient generated will be used for both terrain and player damage.
            # The 'center_strength' of this gradient is self.gradient_center_strength (derived from max_player_damage).
            gradient_start_x, gradient_start_y, effect_gradient_array = create_explosion_gradient(
                impact_position[0], 
                impact_position[1],
                self.explosion_radius,
                self.gradient_center_strength # Use the unified strength for the gradient
            )
            
            self._impact_data = {
                'gradient_origin': (gradient_start_x, gradient_start_y), # Top-left of the gradient
                'effect_gradient': effect_gradient_array, # The numpy array for destruction/damage
                'owner': self.owner,
                'explosion_center': impact_position,
                'explosion_radius': self.explosion_radius
            }
            # GameManager will use 'gradient_origin' and 'effect_gradient' to affect terrain
            # and to calculate damage to players based on overlap.

    def draw(self, screen: pygame.Surface):
        """
        Draws the projectile.
        """
        if self._finished and not self._impact_data: # Don't draw if finished unless it just impacted
            return 
        pygame.draw.circle(screen, (255, 255, 255), (int(self.x), int(self.y)), self.draw_size_radius) # Use instance attribute

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