import pygame
import numpy as np
from typing import Dict, Any, Tuple, List

from .terrain import Terrain, TerrainMap
from .player import Player, PlayerTeam


def simple_explosion_gradient(x: int, y: int, radius: int, center_strength: int) -> Tuple[int, int, np.ndarray]:
    gradient = np.zeros((radius * 2 + 1, radius * 2 + 1), dtype=np.uint8)
    for i in range(-radius, radius + 1):
        for j in range(-radius, radius + 1):
            distance = (i ** 2 + j ** 2) ** 0.5
            if distance <= radius:
                strength = int(center_strength * (1 - distance / radius))
                gradient[i + radius, j + radius] = strength
    start_x = x - radius
    start_y = y - radius
    return start_x, start_y, gradient

class GameManager:
    def __init__(self, config: dict) -> None:
        self.config = config
        self.terrain: Terrain = None
        self.players: List[Player] = []
        self.current_player_index: int = 0
        self.running: bool = False

    def start_new_game(self, map: TerrainMap) -> None:
        self.terrain = Terrain(map, self.config)
        self.players = [] # Clear previous players

        # --- Add players ---
        # TODO: Implement proper starting position calculation based on terrain
        # For now, place them at fixed positions, potentially in the air
        player1_start_pos = (200, 200)
        player2_start_pos = (self.terrain.width - 200, 200)

        player1 = Player(player1_start_pos, PlayerTeam.TEAM_1, self.config)
        player2 = Player(player2_start_pos, PlayerTeam.TEAM_2, self.config)

        self.players.append(player1)
        self.players.append(player2)

        self.current_player_index = 0
        self.running = True

    def next_turn(self) -> None:
        """Advances to the next player's turn."""
        if not self.players:
            return
        # Simple round-robin turn order
        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        print(f"Turn changed to Player {self.current_player_index}")
        # TODO: Add turn timer reset, weapon state changes, etc.

    def get_active_player(self) -> Player | None:
        """Returns the player whose turn it currently is."""
        if self.running and self.players and 0 <= self.current_player_index < len(self.players):
            return self.players[self.current_player_index]
        return None
    
    def update(self, dt: float) -> None:
        """Updates all game components (terrain physics, players, projectiles)."""
        if not self.running:
            return

        # --- Update Players ---
        for player in self.players:
            player.update(dt, self.terrain) # Pass dt and terrain


    def explode(self, x: int, y: int) -> None:
        origin_x, origin_y, gradient = simple_explosion_gradient(x, y, 40, 100)
        self.terrain.destroy_terrain((origin_x, origin_y), gradient)

    def draw_components(self, screen: pygame.Surface) -> None:
        if self.running:
            self.terrain.draw(screen)
            for player in self.players:
                player.draw(screen)