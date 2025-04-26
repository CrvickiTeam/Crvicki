import pygame
import numpy as np
from typing import Dict, Any, Tuple, List, Optional # Add Optional

from .terrain import Terrain, TerrainMap
from .player import Player, PlayerTeam
# Import Weapon base and specific weapons/projectiles
from .weapons.weapon import Weapon
from .weapons.basic_cannon import BasicCannon
# Projectile import might not be directly needed here if Weapon handles drawing

def simple_explosion_gradient(x: int, y: int, radius: int, center_strength: int) -> Tuple[int, int, np.ndarray]:
    # ... (gradient function remains the same) ...
    gradient = np.zeros((radius * 2 + 1, radius * 2 + 1), dtype=np.uint8)
    center_x, center_y = radius, radius
    for i in range(gradient.shape[0]):
        for j in range(gradient.shape[1]):
            dx = i - center_x; dy = j - center_y
            distance = (dx ** 2 + dy ** 2) ** 0.5
            if distance <= radius:
                strength = int(center_strength * (1 - distance / radius))
                gradient[i, j] = strength
    start_x = x - radius; start_y = y - radius
    return start_x, start_y, gradient

class GameManager:
    def __init__(self, config: dict) -> None:
        self.config = config
        self.terrain: Terrain = None
        self.players: List[Player] = []
        self.current_player_index: int = 0
        self.running: bool = False
        # Store the currently active weapon effect (if any)
        self.active_weapon: Optional[Weapon] = None

    # ... (start_new_game remains the same) ...
    def start_new_game(self, map: TerrainMap) -> None:
        self.terrain = Terrain(map, self.config)
        self.players = []
        player1_start_pos = (200, 200)
        player2_start_pos = (self.terrain.width - 200, 200)
        player1 = Player(player1_start_pos, PlayerTeam.TEAM_1, self.config)
        player2 = Player(player2_start_pos, PlayerTeam.TEAM_2, self.config)
        self.players.append(player1)
        self.players.append(player2)
        self.current_player_index = 0
        self.active_weapon = None # Ensure no weapon active at start
        self.running = True
        print("Game started. Player 0's turn.")

    def next_turn(self):
        if not self.players: return
        # Ensure no weapon effect carries over
        self.active_weapon = None
        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        print(f"Turn changed to Player {self.current_player_index}")
        # TODO: Reset turn timer, player state (e.g., allow movement again)

    def get_active_player(self) -> Player | None:
        if self.running and self.players and 0 <= self.current_player_index < len(self.players):
            return self.players[self.current_player_index]
        return None

    def update(self, dt: float) -> None:
        if not self.running: return

        # --- Update Active Weapon Effect ---
        if self.active_weapon:
            self.active_weapon.update(dt, self.terrain)
            if self.active_weapon.is_finished():
                self.active_weapon = None # Clear the finished weapon
                self.next_turn() # Switch turn AFTER weapon effect is done
        else:
            # --- Update Players (only if no weapon is active?) ---
            # Decide if players can move while a projectile is flying.
            # For now, let's allow player updates regardless.
            for player in self.players:
                player.update(dt, self.terrain)

    def explode(self, x: int, y: int) -> None:
        if not self.terrain: return
        # TODO: Add configuration for explosion radius/strength
        radius = 40
        strength = 100
        origin_x, origin_y, gradient = simple_explosion_gradient(x, y, radius, strength)
        self.terrain.destroy_terrain((origin_x, origin_y), gradient)
        # TODO: Check for damage to players within the explosion radius

    def prepare_shot(self, angle: float, power: float):
        """Creates and activates the selected weapon."""
        # Prevent firing if a weapon effect is already active
        if self.active_weapon:
            print("Cannot fire: Weapon effect already in progress.")
            return

        active_player = self.get_active_player()
        if not active_player:
            return

        print(f"Player {self.current_player_index} firing!")
        print(f"  Angle: {angle:.2f} degrees")
        print(f"  Power: {power:.2f}")

        # --- Create and activate the weapon ---
        # TODO: Select weapon based on player's inventory/choice
        # For now, always use BasicCannon
        weapon_instance = BasicCannon(active_player, self)
        weapon_instance.activate(angle, power)

        # Store the active weapon instance
        self.active_weapon = weapon_instance

        # DO NOT switch turn here anymore. Turn switches in update() when weapon.is_finished().


    def draw_components(self, screen: pygame.Surface) -> None:
        if not self.running: return

        # Draw terrain
        if self.terrain: self.terrain.draw(screen)

        # Draw players
        for player in self.players: player.draw(screen)

        # --- Draw Active Weapon Effect (Projectiles) ---
        if self.active_weapon:
            self.active_weapon.draw(screen)

        # Draw active player indicator (only if no weapon is active?)
        # Or maybe always draw it? Your choice.
        if not self.active_weapon:
            active_player = self.get_active_player()
            if active_player:
                indicator_pos = (int(active_player.x), int(active_player.y) - active_player.rect.height // 2 - 10)
                pygame.draw.circle(screen, (255, 255, 0), indicator_pos, 5)
