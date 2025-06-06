import pygame
import math
from typing import TYPE_CHECKING, Tuple

# Import base classes from weapon.py
from .weapon import Weapon, Projectile 

if TYPE_CHECKING:
    from ..player import Player
    from ..game_manager import GameManager

# --- Weapon Class: Sniper ---
class Sniper(Weapon): 
    """
    A weapon that fires a high-damage, small-radius SniperProjectile.
    """
    def __init__(self, owner: 'Player', game_manager: 'GameManager'):
        super().__init__(owner, game_manager) 
        
        weapon_cfg_path = ["game", "weapons", "sniper"] 
        current_config_level = self.game_manager.config
        for key in weapon_cfg_path:
            current_config_level = current_config_level.get(key, {})
        
        # Sniper specific parameters
        self.explosion_radius_val: int = int(current_config_level.get("explosion_radius", 5)) # Tiny radius
        self.center_damage_val: int = int(current_config_level.get("center_damage", 85))   # High damage
        
        # Sniper might have a very high power_to_velocity_scale for a fast projectile
        self.power_to_velocity_scale: float = float(current_config_level.get("power_to_velocity_scale", self.default_power_to_velocity_scale))
        
        # Projectile properties
        self.proj_gravity_val: float = float(current_config_level.get("projectile_gravity", self.default_projectile_gravity))
        # Sniper projectile might be very small or even invisible (draw_size_radius 0 or 1)
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

        projectile = SniperProjectile(
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

# --- Projectile Class: SniperProjectile ---
class SniperProjectile(Projectile): 
    """
    The specific projectile fired by the Sniper weapon.
    Characterized by a very small explosion radius and high center damage.
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
        # Sniper projectile might have unique properties if needed, e.g., faster update,
        # or different collision logic if it's meant to be a "hitscan-like" effect.
        # For now, it behaves like a standard projectile with extreme parameters.