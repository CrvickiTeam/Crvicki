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
        # Add list for projectiles later
        # self.projectiles: List[Projectile] = []

    # ... (start_new_game, next_turn, get_active_player remain the same) ...
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
        self.running = True
        print("Game started. Player 0's turn.")

    def next_turn(self):
        if not self.players: return
        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        print(f"Turn changed to Player {self.current_player_index}")

    def get_active_player(self) -> Player | None:
        if self.running and self.players and 0 <= self.current_player_index < len(self.players):
            return self.players[self.current_player_index]
        return None

    def update(self, dt: float) -> None:
        if not self.running: return
        for player in self.players:
            player.update(dt, self.terrain)
        # Update projectiles later
        # for projectile in self.projectiles:
        #     projectile.update(dt, self.terrain)

    def explode(self, x: int, y: int) -> None:
        if not self.terrain: return
        origin_x, origin_y, gradient = simple_explosion_gradient(x, y, 40, 100)
        self.terrain.destroy_terrain((origin_x, origin_y), gradient)

    # --- Add method to handle shot preparation ---
    def prepare_shot(self, angle: float, power: float):
        """Receives shot info from the active player."""
        active_player = self.get_active_player()
        if not active_player:
            return

        print(f"Player {self.current_player_index} firing!")
        print(f"  Angle: {angle:.2f} degrees")
        print(f"  Power: {power:.2f}")

        # --- TODO: Create and launch projectile ---
        # start_pos = (active_player.x, active_player.y) # Adjust based on weapon position
        # initial_velocity_x = power * math.cos(math.radians(angle))
        # initial_velocity_y = -power * math.sin(math.radians(angle)) # Negative for pygame y-axis
        # projectile = Projectile(start_pos, initial_velocity_x, initial_velocity_y, ...)
        # self.projectiles.append(projectile)

        # --- Switch turn after firing ---
        self.next_turn()


    def draw_components(self, screen: pygame.Surface) -> None:
        if not self.running: return
        if self.terrain: self.terrain.draw(screen)
        for player in self.players: player.draw(screen)
        # Draw projectiles later
        # for projectile in self.projectiles: projectile.draw(screen)

        # Draw active player indicator
        active_player = self.get_active_player()
        if active_player:
            indicator_pos = (int(active_player.x), int(active_player.y) - active_player.rect.height // 2 - 10)
            pygame.draw.circle(screen, (255, 255, 0), indicator_pos, 5)
