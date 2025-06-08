from __future__ import annotations
import pygame 
import math 
import numpy as np
from typing import List, TYPE_CHECKING, Dict, Any, Optional, Tuple
from enum import Enum

# Add this import
from ..terrain import TerrainMaterial # <<< ADD THIS LINE

if TYPE_CHECKING:
    from ..player import Player
    from ..terrain import Terrain # This is for type hinting, TerrainMaterial needs direct import
    from ..game_manager import GameManager

class WeaponType(Enum): # <<< NEW ENUM
    SMALL_BOMB = 0
    BIG_BOMB = 1
    SNIPER = 2
    SALVO = 3
    # Add more weapon types here in the future

    def display_name(self) -> str:
        return self.name.replace("_", " ").title()

# Helper for ordered access, useful for UI and selection by number
WEAPON_TYPES_ORDERED: List[WeaponType] = [
    WeaponType.SMALL_BOMB,
    WeaponType.BIG_BOMB,
    WeaponType.SNIPER,
    WeaponType.SALVO
]


# --- Base Weapon Class ---
class Weapon:
    """Base class for all weapons."""

    def __init__(self, owner: 'Player', game_manager: 'GameManager'): 
        self.owner = owner
        self.game_manager = game_manager 
        self.projectiles: List['Projectile'] = [] # Projectile is now defined above
        self._is_finished = True 

        weapon_defaults_cfg = self.game_manager.config.get("game", {}).get("weapons", {}).get("defaults", {})
        self.default_power_to_velocity_scale: float = float(weapon_defaults_cfg.get("power_to_velocity_scale", 5.0))
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
                 center_damage: int, # This is the configured center damage for the weapon
                 gravity: float,
                 draw_size_radius: int):
        self.x, self.y = start_pos
        self.vx = initial_vx
        self.vy = initial_vy
        self.owner = owner 
        self.game_manager = game_manager 
        self._finished = False 
        self._impact_data: Optional[Dict[str, Any]] = None
        self.directly_hit_player_this_frame: Optional[Player] = None # <<< NEW: To store directly hit player

        self.gravity: float = gravity
        self.draw_size_radius: int = draw_size_radius 
        self.explosion_radius = explosion_radius
        self.gradient_center_strength = center_damage # This is the configured center_damage

        weapon_defaults_cfg = self.game_manager.config.get("game", {}).get("weapons", {}).get("defaults", {})
        self.sub_step_radius_factor: float = float(weapon_defaults_cfg.get("sub_step_radius_factor", 0.5))
        self.min_sub_step_size: float = float(weapon_defaults_cfg.get("min_sub_step_size", 1.0))
        self.max_sub_steps_per_frame: int = int(weapon_defaults_cfg.get("max_sub_steps_per_frame", 100))


    def update(self, dt: float, terrain: 'Terrain'): 
        if self._finished:
            return
        
        self.directly_hit_player_this_frame = None 

        start_x_this_frame = self.x
        start_y_this_frame = self.y

        total_dx = self.vx * dt
        total_dy = self.vy * dt 
        
        self.vy += self.gravity * dt 

        distance_to_move = math.sqrt(total_dx**2 + total_dy**2)
        step_size = max(self.min_sub_step_size, float(self.draw_size_radius) * self.sub_step_radius_factor) 

        num_sub_steps = 0
        if distance_to_move > 0: 
            num_sub_steps = int(math.ceil(distance_to_move / step_size))
            num_sub_steps = min(num_sub_steps, self.max_sub_steps_per_frame) 
        
        sub_dx: float = 0.0
        sub_dy: float = 0.0

        if num_sub_steps == 0: 
            num_sub_steps = 1 
        elif num_sub_steps > 0 : 
            sub_dx = total_dx / num_sub_steps
            sub_dy = total_dy / num_sub_steps

        if num_sub_steps == 1: # If only one step, or if num_sub_steps was 0 and became 1
            sub_dx = total_dx
            sub_dy = total_dy
        # If num_sub_steps was 0 and became 1, total_dx/dy might be 0, so sub_dx/dy will be 0. Correct.

        collided_this_frame = False
        impact_position: Tuple[int, int] = (int(start_x_this_frame + total_dx), int(start_y_this_frame + total_dy)) 

        current_valid_x = start_x_this_frame
        current_valid_y = start_y_this_frame

        for i in range(num_sub_steps):
            point_to_check_x = current_valid_x + sub_dx
            point_to_check_y = current_valid_y + sub_dy

            proj_cx_check: float = point_to_check_x
            proj_cy_check: float = point_to_check_y
            
            # --- Player Collision Check ---
            for player_target in self.game_manager.players:
                if player_target is not self.owner and player_target.alive:
                    player_cx: float = player_target.x
                    player_cy: float = player_target.y
                    player_radius: float = player_target.radius
                    projectile_collision_radius: float = float(self.draw_size_radius)
                    dx_p: float = proj_cx_check - player_cx
                    dy_p: float = proj_cy_check - player_cy
                    distance_squared_p: float = dx_p*dx_p + dy_p*dy_p
                    sum_radii_p: float = projectile_collision_radius + player_radius
                    sum_radii_squared_p: float = sum_radii_p * sum_radii_p

                    if distance_squared_p < sum_radii_squared_p:
                        collided_this_frame = True
                        self.directly_hit_player_this_frame = player_target 
                        self.x = current_valid_x 
                        self.y = current_valid_y
                        impact_position = (int(proj_cx_check), int(proj_cy_check)) 
                        break 
            if collided_this_frame:
                break 

            # --- Boundary and Terrain Collision Check ---
            check_x, check_y = int(proj_cx_check), int(proj_cy_check)
            
            # Check for destructive boundaries (Left, Right, Bottom)
            # Projectiles can go off the top (check_y < 0) and continue.
            if check_x < 0 or check_x >= terrain.width or check_y >= terrain.height:
                collided_this_frame = True
                self.x = current_valid_x 
                self.y = current_valid_y
                impact_position = (check_x, check_y) 
                # print(f"Projectile hit L/R/Bottom boundary at impact {impact_position}, resting at ({self.x},{self.y})")
                break 

            # If not hit a destructive boundary, check for terrain collision,
            # but only if the projectile is within the terrain's y-bounds (0 to terrain.height -1).
            # If check_y < 0, it's above the screen, so skip terrain check.
            if 0 <= check_y < terrain.height: # Horizontal bounds (0 <= check_x < terrain.width) are implied if previous boundary check didn't trigger
                # Clamping check_x here is a safeguard, though it should be within bounds if the L/R boundary check passed.
                safe_check_x = min(max(0, check_x), terrain.width - 1)
                # check_y is already confirmed to be within [0, terrain.height - 1]
                if terrain.logic_grid[safe_check_x, check_y] != TerrainMaterial.EMPTY.value: 
                    collided_this_frame = True
                    self.x = current_valid_x 
                    self.y = current_valid_y
                    impact_position = (check_x, check_y) 
                    # print(f"Projectile hit terrain at impact {impact_position}, resting at ({self.x},{self.y})")
                    break 
            
            current_valid_x = point_to_check_x
            current_valid_y = point_to_check_y
        
        if not collided_this_frame: 
            self.x = current_valid_x 
            self.y = current_valid_y

        if collided_this_frame:
            self._finished = True
            clamped_impact_x = min(max(0, impact_position[0]), terrain.width -1)
            clamped_impact_y = min(max(0, impact_position[1]), terrain.height -1)

            gradient_start_x, gradient_start_y, effect_gradient_array = create_explosion_gradient(
                clamped_impact_x, 
                clamped_impact_y,
                self.explosion_radius,
                self.gradient_center_strength 
            )
            self._impact_data = {
                'gradient_origin': (gradient_start_x, gradient_start_y),
                'effect_gradient': effect_gradient_array,
                'owner': self.owner,
                'explosion_center': (clamped_impact_x, clamped_impact_y), 
                'explosion_radius': self.explosion_radius,
                'directly_hit_player': self.directly_hit_player_this_frame, 
                'configured_center_damage': self.gradient_center_strength   
            }

    def draw(self, screen: pygame.Surface) -> None:
        if self._finished:
            return

        screen_width, screen_height = screen.get_size()

        if self.y < 0:
            arrow_color = (255, 0, 0)
            arrow_size = 8
            arrow_height = 10
            arrow_top_y = 5
            arrow_x = min(max(self.x, arrow_size), screen_width - arrow_size)
            points = [
                (arrow_x, arrow_top_y),
                (arrow_x - arrow_size, arrow_top_y + arrow_height),
                (arrow_x + arrow_size, arrow_top_y + arrow_height)
            ]
            pygame.draw.polygon(screen, arrow_color, points)
        elif 0 <= self.x < screen_width and 0 <= self.y < screen_height:
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