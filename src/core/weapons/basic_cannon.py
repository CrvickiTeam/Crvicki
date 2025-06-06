import pygame
import math
from typing import TYPE_CHECKING, Tuple

from .weapon import Weapon 
from ..projectiles.basic_projectile import BasicProjectile # Or just Projectile if BasicProjectile is very simple

if TYPE_CHECKING:
    from ..player import Player
    from ..game_manager import GameManager

class BasicCannon(Weapon):
    """
    A simple weapon that fires a single BasicProjectile.
    """
    # If BasicCannon needed a *different* scale, you could override it here:
    # POWER_TO_VELOCITY_SCALE = 0.8 # Example override

    def __init__(self, owner: 'Player', game_manager: 'GameManager'):
        super().__init__(owner, game_manager) # game_manager is passed to base
        
        # Load BasicCannon specific config
        # Example: self.game_manager.config['game']['weapons']['basic_cannon']
        cannon_cfg_path = ["game", "weapons", "basic_cannon"] 
        current_config_level = self.game_manager.config
        for key in cannon_cfg_path:
            current_config_level = current_config_level.get(key, {})
        
        # Default values if not found in config
        self.explosion_radius_val: int = int(current_config_level.get("explosion_radius", 30))
        self.center_damage_val: int = int(current_config_level.get("center_damage", 50))
        
        # Override power_to_velocity_scale if specified for this specific weapon type
        # The base Weapon.__init__ already loads a default power_to_velocity_scale.
        # This allows specific weapons to have their own.
        if "power_to_velocity_scale" in current_config_level:
             self.power_to_velocity_scale = float(current_config_level["power_to_velocity_scale"])


    def activate(self, angle: float, power: float):
        super().activate(angle, power) # Call base to reset projectiles and _is_finished

        if self._is_finished: 
            return

        angle_rad = math.radians(angle)
        velocity_magnitude = power * self.power_to_velocity_scale # Use instance variable
        initial_vx = velocity_magnitude * math.cos(angle_rad)
        initial_vy = -velocity_magnitude * math.sin(angle_rad)

        start_pos: Tuple[float, float] = (self.owner.x, self.owner.y) 

        projectile = BasicProjectile( # Or just Projectile if BasicProjectile doesn't add much
            start_pos, 
            initial_vx, 
            initial_vy, 
            self.owner,
            self.game_manager,
            explosion_radius=self.explosion_radius_val, # Pass configured radius
            center_damage=self.center_damage_val      # Pass configured damage
        )
        self.projectiles.append(projectile)
        # self._is_finished is already False due to super().activate()

    # update() is inherited from Weapon
    # draw() is inherited from Weapon
    # is_finished() is inherited from Weapon
