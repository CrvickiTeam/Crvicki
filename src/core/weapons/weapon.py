from __future__ import annotations
import pygame 
import math 
import numpy as np # Added for create_explosion_gradient
from typing import List, TYPE_CHECKING, Dict, Any, Optional, Tuple # Added Optional, Tuple, np

if TYPE_CHECKING:
    from ..player import Player
    from ..terrain import Terrain
    from ..game_manager import GameManager
    # Projectile will be defined in this file, so no forward ref needed for it here if defined before Weapon
    # However, if Weapon is defined first, or for clarity, it can be kept.

# --- Base Weapon Class ---
class Weapon:
    """Base class for all weapons."""

    def __init__(self, owner: 'Player', game_manager: 'GameManager'): 
        self.owner = owner
        self.game_manager = game_manager 
        self.projectiles: List['Projectile'] = [] # Projectile is now defined above
        self._is_finished = True 

        weapon_defaults_cfg = self.game_manager.config.get("game", {}).get("weapons", {}).get("defaults", {})
        self.power_to_velocity_scale: float = float(weapon_defaults_cfg.get("power_to_velocity_scale", 5.0))
        self.default_projectile_gravity: float = float(weapon_defaults_cfg.get("projectile_gravity", 400.0))
        self.default_projectile_draw_size_radius: int = int(weapon_defaults_cfg.get("projectile_draw_size_radius", 5))

    def activate(self, angle: float, power: float):
        self.projectiles = []
        self._is_finished = False

    def update(self, dt: float, terrain: 'Terrain', game_manager_ref: 'GameManager'):
        if self._is_finished:
            return

        for i in range(len(self.projectiles) - 1, -1, -1):
            proj = self.projectiles[i]
            proj.update(dt, terrain) 
            if proj.is_finished():
                impact_data = proj.get_impact_data()
                if impact_data:
                    game_manager_ref.process_impact_effect(impact_data)
                self.projectiles.pop(i) 
        if not self.projectiles: 
            self._is_finished = True

    def draw(self, screen: pygame.Surface):
        for proj in self.projectiles:
            proj.draw(screen)

    def is_finished(self) -> bool:
        return self._is_finished
    


# --- Base Projectile Class (moved from projectile.py) ---
class Projectile:
    """Base class for projectiles."""

    def __init__(self, start_pos: tuple[float, float], initial_vx: float, initial_vy: float, owner: 'Player',
                 game_manager: 'GameManager', 
                 explosion_radius: int,
                 center_damage: int,
                 gravity: float,
                 draw_size_radius: int):
        self.x, self.y = start_pos
        self.vx = initial_vx
        self.vy = initial_vy
        self.owner = owner 
        self.game_manager = game_manager 
        self._finished = False 
        self._impact_data: Optional[Dict[str, Any]] = None

        self.gravity: float = gravity
        self.draw_size_radius: int = draw_size_radius
        self.explosion_radius = explosion_radius
        self.gradient_center_strength = center_damage

    def update(self, dt: float, terrain: 'Terrain'): 
        if self._finished:
            return

        self.vy += self.gravity * dt
        self.x += self.vx * dt
        self.y += self.vy * dt

        proj_point = (int(self.x), int(self.y))
        
        collided_this_frame = False
        impact_position: Tuple[int, int] = proj_point
        
        for player in self.game_manager.players:
            if player is not self.owner and player.alive:
                if player.rect.collidepoint(proj_point):
                    collided_this_frame = True
                    break 

        if not collided_this_frame:
            check_x, check_y = proj_point
            if not (0 <= check_x < terrain.width and check_y < terrain.height):
                collided_this_frame = True
            elif check_y >= 0:
                if terrain.logic_grid[min(check_x, terrain.width-1), min(check_y, terrain.height-1)] != 0: 
                    collided_this_frame = True
        
        if collided_this_frame:
            self._finished = True
            gradient_start_x, gradient_start_y, effect_gradient_array = create_explosion_gradient(
                impact_position[0], 
                impact_position[1],
                self.explosion_radius,
                self.gradient_center_strength
            )
            self._impact_data = {
                'gradient_origin': (gradient_start_x, gradient_start_y),
                'effect_gradient': effect_gradient_array,
                'owner': self.owner,
                'explosion_center': impact_position,
                'explosion_radius': self.explosion_radius
            }

    def draw(self, screen: pygame.Surface):
        if self._finished and not self._impact_data:
            return 
        pygame.draw.circle(screen, (255, 255, 255), (int(self.x), int(self.y)), self.draw_size_radius)

    def is_finished(self) -> bool:
        return self._finished

    def get_impact_data(self) -> Optional[Dict[str, Any]]:
        return self._impact_data
    


# --- Helper function for generating explosion gradient (moved from projectile.py) ---
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
    if radius < 0: 
        radius = 0
    if radius == 0: 
        gradient_array = np.array([[center_strength]], dtype=np.uint8)
        return x, y, gradient_array
        
    diameter = radius * 2 + 1
    gradient_array = np.zeros((diameter, diameter), dtype=np.uint8)
    grad_center_x, grad_center_y = radius, radius 

    for i in range(diameter):
        for j in range(diameter):
            dx_grad = i - grad_center_x # Renamed to avoid conflict if dx, dy are used elsewhere
            dy_grad = j - grad_center_y # Renamed
            distance = math.sqrt(dx_grad**2 + dy_grad**2) 
            if distance <= radius: 
                strength_val = int(center_strength * max(0, (1 - distance / radius)))
                gradient_array[i, j] = np.clip(strength_val, 0, 255)
    
    world_start_x = x - radius
    world_start_y = y - radius
    return world_start_x, world_start_y, gradient_array