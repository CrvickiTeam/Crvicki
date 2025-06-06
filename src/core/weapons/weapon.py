from __future__ import annotations
import pygame
import math # Import math here if it's used for default calculations in base Weapon
from typing import List, TYPE_CHECKING

# Use TYPE_CHECKING to avoid circular imports for type hints
if TYPE_CHECKING:
    from ..player import Player
    from ..terrain import Terrain
    from ..game_manager import GameManager
    from ..projectiles.projectile import Projectile 

class Weapon:
    """Base class for all weapons."""

    # Default power scaling factor for all weapons.
    # Subclasses can override this if they have different launch mechanics.
    POWER_TO_VELOCITY_SCALE: float = 5 # Using the value from BasicCannon as default

    def __init__(self, owner: 'Player', game_manager: 'GameManager'):
        """
        Initializes the weapon.

        Args:
            owner: The player who owns/fired this weapon.
            game_manager: Reference to the game manager (passed to update).
        """
        self.owner = owner
        self.projectiles: List['Projectile'] = [] 
        self._is_finished = False 

    def activate(self, angle: float, power: float):
        """
        Starts the weapon's action (e.g., launching projectiles).
        This method should be implemented by subclasses.
        It typically involves calculating initial velocity based on angle, power,
        and self.POWER_TO_VELOCITY_SCALE.

        Args:
            angle: The launch angle in degrees.
            power: The launch power.
        """
        raise NotImplementedError("Subclasses must implement activate()")

    def update(self, dt: float, terrain: 'Terrain', game_manager: 'GameManager'):
        """
        Updates the state of the weapon and its projectiles.
        If a projectile is finished, its impact data is processed via the GameManager.
        Checks if the weapon's action is complete.

        Args:
            dt: Delta time since the last frame.
            terrain: The game terrain for collision checks.
            game_manager: The game manager to process impact effects.
        """
        if self._is_finished:
            return

        # Iterate backwards if removing items
        for i in range(len(self.projectiles) - 1, -1, -1):
            proj = self.projectiles[i]
            proj.update(dt, terrain) 

            if proj.is_finished():
                impact_data = proj.get_impact_data()
                if impact_data:
                    game_manager.process_impact_effect(impact_data)
                
                self.projectiles.pop(i) 

        # Check if the weapon's action is complete (e.g., all projectiles are gone)
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
