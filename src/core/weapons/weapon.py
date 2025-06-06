from __future__ import annotations
import pygame 
import math 
from typing import List, TYPE_CHECKING, Dict, Any # Added Dict, Any

# Use TYPE_CHECKING to avoid circular imports for type hints
if TYPE_CHECKING:
    from ..player import Player
    from ..terrain import Terrain
    from ..game_manager import GameManager
    from ..projectiles.projectile import Projectile 

class Weapon:
    """Base class for all weapons."""

    def __init__(self, owner: 'Player', game_manager: 'GameManager'): # <<< ADD game_manager
        self.owner = owner
        self.game_manager = game_manager # Store game_manager
        self.projectiles: List['Projectile'] = [] 
        self._is_finished = True # Default state as per typical weapon logic

        # Load weapon defaults from config
        weapon_defaults_cfg = self.game_manager.config.get("game", {}).get("weapons", {}).get("defaults", {})
        self.power_to_velocity_scale: float = float(weapon_defaults_cfg.get("power_to_velocity_scale", 5.0))

    def activate(self, angle: float, power: float):
        """
        Base activate method. Resets projectiles and sets weapon to not finished.
        Subclasses should call this if they override.
        """
        self.projectiles = []
        self._is_finished = False
        # Subclasses will add projectiles after calling super().activate() or manage _is_finished themselves.

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
        """
        Draws any visual representation of the weapon's effect (e.g., its projectiles).

        Args:
            screen: The pygame surface to draw on.
        """
        for proj in self.projectiles:
            proj.draw(screen)

    def is_finished(self) -> bool:
        """
        Returns True if the weapon's action and all its effects are complete.
        """
        return self._is_finished
