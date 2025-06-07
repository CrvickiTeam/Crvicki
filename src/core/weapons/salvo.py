import pygame
import math
import random 
from typing import TYPE_CHECKING, Tuple

from .weapon import Weapon, Projectile 

if TYPE_CHECKING:
    from ..player import Player
    from ..game_manager import GameManager
    from ..terrain import Terrain

# --- Weapon Class: Salvo ---  // <<< RENAMED
class Salvo(Weapon): 
    """
    A weapon that fires a salvo of multiple small projectiles in rapid succession,
    with some variability in angle and power for each shot.
    (Formerly RapidFire)
    """
    def __init__(self, owner: 'Player', game_manager: 'GameManager'):
        super().__init__(owner, game_manager) 
        
        weapon_cfg_path = ["game", "weapons", "salvo"] # <<< UPDATED config path key
        current_config_level = self.game_manager.config
        for key in weapon_cfg_path:
            current_config_level = current_config_level.get(key, {})
        
        self.num_projectiles_to_fire_total: int = int(current_config_level.get("num_projectiles", 10))
        self.shot_delay_val: float = float(current_config_level.get("shot_delay", 0.1)) 
        self.angle_spread_val: float = float(current_config_level.get("angle_spread", 5.0)) 
        self.power_spread_percentage_val: float = float(current_config_level.get("power_spread_percentage", 0.1))

        self.proj_explosion_radius_val: int = int(current_config_level.get("explosion_radius", 10))
        self.proj_center_damage_val: int = int(current_config_level.get("center_damage", 15))
        
        self.power_to_velocity_scale: float = float(current_config_level.get("power_to_velocity_scale", self.default_power_to_velocity_scale))
        self.proj_gravity_val: float = float(current_config_level.get("projectile_gravity", self.default_projectile_gravity))
        self.proj_draw_size_radius_val: int = int(current_config_level.get("projectile_draw_size_radius", self.default_projectile_draw_size_radius))

        self._projectiles_fired_count: int = 0
        self._time_since_last_shot: float = 0.0
        self._is_firing_salvo: bool = False
        self._base_angle: float = 0.0
        self._base_power: float = 0.0
        
    def activate(self, angle: float, power: float):
        self.projectiles = [] 
        self._is_finished = False 

        self._base_angle = angle
        self._base_power = power
        self._projectiles_fired_count = 0
        self._time_since_last_shot = self.shot_delay_val 
        self._is_firing_salvo = True

    def _fire_one_projectile(self):
        angle_offset = random.uniform(-self.angle_spread_val, self.angle_spread_val)
        current_angle = self._base_angle + angle_offset
        power_offset_factor = random.uniform(-self.power_spread_percentage_val, self.power_spread_percentage_val)
        current_power = self._base_power * (1.0 + power_offset_factor)

        angle_rad = math.radians(current_angle)
        velocity_magnitude = current_power * self.power_to_velocity_scale 
        initial_vx = velocity_magnitude * math.cos(angle_rad)
        initial_vy = -velocity_magnitude * math.sin(angle_rad)

        start_pos: Tuple[float, float] = (self.owner.x, self.owner.y) 

        projectile = SalvoProjectile( # <<< RENAMED Projectile class
            start_pos, 
            initial_vx, 
            initial_vy, 
            self.owner,
            self.game_manager,
            explosion_radius=self.proj_explosion_radius_val,
            center_damage=self.proj_center_damage_val,
            gravity=self.proj_gravity_val,
            draw_size_radius=self.proj_draw_size_radius_val
        )
        self.projectiles.append(projectile)
        self._projectiles_fired_count += 1

    def update(self, dt: float, terrain: 'Terrain', game_manager_ref: 'GameManager'):
        if self._is_firing_salvo:
            self._time_since_last_shot += dt
            if self._projectiles_fired_count < self.num_projectiles_to_fire_total and \
               self._time_since_last_shot >= self.shot_delay_val:
                self._fire_one_projectile()
                self._time_since_last_shot = 0.0 
            
            if self._projectiles_fired_count >= self.num_projectiles_to_fire_total:
                self._is_firing_salvo = False 

        for i in range(len(self.projectiles) - 1, -1, -1):
            proj = self.projectiles[i]
            proj.update(dt, terrain) 
            if proj.is_finished():
                impact_data = proj.get_impact_data()
                if impact_data:
                    game_manager_ref.process_impact_effect(impact_data)
                self.projectiles.pop(i) 
        
        if not self._is_firing_salvo and not self.projectiles:
            self._is_finished = True

# --- Projectile Class: SalvoProjectile --- // <<< RENAMED
class SalvoProjectile(Projectile): 
    """
    A small projectile used by the Salvo weapon.
    (Formerly RapidFireProjectile)
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