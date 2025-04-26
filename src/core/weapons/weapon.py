from __future__ import annotations
import pygame
from typing import List, TYPE_CHECKING

# Use TYPE_CHECKING to avoid circular imports for type hints
if TYPE_CHECKING:
    from ..player import Player
    from ..terrain import Terrain
    from ..game_manager import GameManager
    from ..projectiles.projectile import Projectile # Assuming a base Projectile class exists

class Weapon:
    """Base class for all weapons."""

    def __init__(self, owner: Player, game_manager: GameManager):
        """
        Initializes the weapon.

        Args:
            owner: The player who owns/fired this weapon.
            game_manager: Reference to the game manager for interactions (e.g., explosions).
        """
        self.owner = owner
        self.game_manager = game_manager
        self.projectiles: List['Projectile'] = [] # List to hold active projectiles managed by this weapon instance
        self._is_finished = False # Flag to indicate if the weapon's action is complete

    def activate(self, angle: float, power: float):
        """
        Starts the weapon's action (e.g., launching projectiles).
        This method should be implemented by subclasses.

        Args:
            angle: The launch angle in degrees.
            power: The launch power.
        """
        # Example: Subclasses would create and add projectiles here
        # projectile = SomeProjectile(...)
        # self.projectiles.append(projectile)
        raise NotImplementedError("Subclasses must implement activate()")

    def update(self, dt: float, terrain: Terrain):
        """
        Updates the state of the weapon and its projectiles.
        Checks if the weapon's action is complete.

        Args:
            dt: Delta time since the last frame.
            terrain: The game terrain for collision checks.
        """
        if self._is_finished:
            return

        # Update all active projectiles managed by this weapon
        # Iterate backwards if removing items
        for i in range(len(self.projectiles) - 1, -1, -1):
            proj = self.projectiles[i]
            proj.update(dt, terrain, self.game_manager)
            # Check if the projectile itself is finished (collided, out of bounds, etc.)
            if proj.is_finished():
                # Optional: Handle projectile destruction effects here if needed
                # Remove the finished projectile from the list
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
