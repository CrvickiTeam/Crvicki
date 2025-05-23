import pygame
import numpy as np
import math
from typing import Dict, Any, Tuple, List, Optional

from .terrain import Terrain, TerrainMap
from .player import Player, PlayerTeam
from .weapons.weapon import Weapon
from .weapons.basic_cannon import BasicCannon

def simple_explosion_gradient(x: int, y: int, radius: int, center_strength: int) -> Tuple[int, int, np.ndarray]:
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
        self.active_weapon: Optional[Weapon] = None

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
        self.active_weapon = None
        self.running = True
        print("Game started. Player 0's turn.")

    def next_turn(self):
        if not self.players: return
        self.active_weapon = None
        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        print(f"Turn changed to Player {self.current_player_index}")

    def get_active_player(self) -> Player | None:
        if self.running and self.players and 0 <= self.current_player_index < len(self.players):
            return self.players[self.current_player_index]
        return None

    def update(self, dt: float) -> None:
        if not self.running: return
        if self.active_weapon:
            self.active_weapon.update(dt, self.terrain)
            if self.active_weapon.is_finished():
                self.active_weapon = None
                self.next_turn()
        else:
            for player in self.players:
                player.update(dt, self.terrain)

    def explode(self, x: int, y: int, owner=None) -> None:
        if not self.terrain: return
        radius = 25
        strength = 100
        origin_x, origin_y, gradient = simple_explosion_gradient(x, y, radius, strength)
        self.terrain.destroy_terrain((origin_x, origin_y), gradient)
        explosion_pos = (x, y)
        max_damage = 50  # prilagodi po želji

        for player in self.players:
            if not player.alive or player == owner:
                continue
            dx = player.x - explosion_pos[0]
            dy = player.y - explosion_pos[1]
            distance = math.hypot(dx, dy)

            if distance < radius:
                damage = int(max_damage * (1 - distance / radius))
                player.apply_damage(damage)
                print(f"Player {player.team.name} took {damage} damage! Remaining HP: {player.health}")

    def prepare_shot(self, angle: float, power: float):
        if self.active_weapon:
            print("Cannot fire: Weapon effect already in progress.")
            return

        active_player = self.get_active_player()
        if not active_player:
            return

        print(f"Player {self.current_player_index} firing!")
        print(f"  Angle: {angle:.2f} degrees")
        print(f"  Power: {power:.2f}")


        weapon_instance = BasicCannon(active_player, self)
        weapon_instance.activate(angle, power)
        self.active_weapon = weapon_instance


    def draw_components(self, screen: pygame.Surface) -> None:
        if not self.running: return
        if self.terrain: self.terrain.draw(screen)
        for player in self.players: player.draw(screen)
        if self.active_weapon: self.active_weapon.draw(screen)

        if not self.active_weapon:
            active_player = self.get_active_player()
            if active_player:
                indicator_pos = (int(active_player.x), int(active_player.y) - active_player.rect.height // 2 - 10)
                pygame.draw.circle(screen, (255, 255, 0), indicator_pos, 5)
