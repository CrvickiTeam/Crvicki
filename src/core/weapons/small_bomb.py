import pygame
import math
from typing import TYPE_CHECKING, Tuple

# Import base classes from the modified weapon.py
from .weapon import Weapon, Projectile 

if TYPE_CHECKING:
    from ..player import Player
    from ..game_manager import GameManager

# --- Weapon Class: SmallBomb ---
class SmallBomb(Weapon): 
    """
    A weapon that fires a single SmallBombProjectile.
    (Formerly BasicCannon)
    """
    def __init__(self, owner: 'Player', game_manager: 'GameManager'):
        super().__init__(owner, game_manager) 
        
        # Ensure your config.json has a "small_bomb" section under "game.weapons"
        # or update this path if you keep "basic_cannon" as the config key.
        weapon_cfg_path = ["game", "weapons", "small_bomb"] 
        current_config_level = self.game_manager.config
        for key in weapon_cfg_path:
            current_config_level = current_config_level.get(key, {})
        
        self.explosion_radius_val: int = int(current_config_level.get("explosion_radius", 25)) # Example default
        self.center_damage_val: int = int(current_config_level.get("center_damage", 40))   # Example default

        self.power_to_velocity_scale: float = float(current_config_level.get("power_to_velocity_scale", self.default_power_to_velocity_scale))
        self.proj_gravity_val: float = float(current_config_level.get("projectile_gravity", self.default_projectile_gravity))
        self.proj_draw_size_radius_val: int = int(current_config_level.get("projectile_draw_size_radius", self.default_projectile_draw_size_radius))

    def activate(self, angle: float, power: float):
        super().activate(angle, power) 

        if self._is_finished: 
            return

        angle_rad = math.radians(angle)
        velocity_magnitude = power * self.power_to_velocity_scale
        initial_vx = velocity_magnitude * math.cos(angle_rad)
        initial_vy = -velocity_magnitude * math.sin(angle_rad)

        start_pos: Tuple[float, float] = (self.owner.x, self.owner.y) 

        projectile = SmallBombProjectile( # Changed from BasicProjectile
            start_pos, 
            initial_vx, 
            initial_vy, 
            self.owner,
            self.game_manager,
            explosion_radius=self.explosion_radius_val,
            center_damage=self.center_damage_val,
            gravity=self.proj_gravity_val,
            draw_size_radius=self.proj_draw_size_radius_val
        )
        self.projectiles.append(projectile)

# --- Projectile Class: SmallBombProjectile ---
class SmallBombProjectile(Projectile): 
    """
    The specific projectile fired by the SmallBomb weapon.
    (Formerly BasicProjectile)
    """
    def __init__(self, start_pos: tuple[float, float], initial_vx: float, initial_vy: float, 
                 owner: 'Player',
                 game_manager: 'GameManager',
                 explosion_radius: int,
                 center_damage: int,
                 gravity: float,
                 draw_size_radius: int):
        
        super().__init__(start_pos, initial_vx, initial_vy, owner,
                         game_manager, 
                         explosion_radius=explosion_radius,
                         center_damage=center_damage,
                         gravity=gravity,
                         draw_size_radius=draw_size_radius)
        # Any specific logic for SmallBombProjectile would go here.