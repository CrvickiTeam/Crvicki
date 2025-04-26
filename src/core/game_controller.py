import pygame
import numpy as np
from typing import Dict, Any, Tuple

from .terrain import Terrain, TerrainMap


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

class GameController:
    def __init__(self, config: dict) -> None:
        self.config = config
        self.terrain: Terrain = None
        self.running: bool = False

    def start_new_game(self, map: TerrainMap) -> None:
        self.terrain = Terrain(map, self.config)
        self.running = True

    def explode(self, x: int, y: int) -> None:
        origin_x, origin_y, gradient = simple_explosion_gradient(x, y, 40, 100)
        self.terrain.destroy_terrain((origin_x, origin_y), gradient)

    def draw_components(self, screen: pygame.Surface) -> None:
        if self.running:
            self.terrain.draw(screen)