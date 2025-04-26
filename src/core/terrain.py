import pygame
import numpy as np
from typing import Dict, Any, Tuple
from enum import Enum


class TerrainMaterial(Enum):
    EMPTY = 0
    GRASS = 1
    SOIL = 2
    STONE = 3
    BEDROCK = 4

class TerrainMap(Enum):
    FLAT = 0

MATERIAL_COLOR = {
    TerrainMaterial.EMPTY: (0, 0, 0, 0),
    TerrainMaterial.GRASS: (0, 255, 0),
    TerrainMaterial.SOIL: (139, 69, 19),
    TerrainMaterial.STONE: (128, 128, 128),
    TerrainMaterial.BEDROCK: (105, 105, 105)
}
MATERIAL_HARDNESS = {
    TerrainMaterial.EMPTY: 0,
    TerrainMaterial.GRASS: 10,
    TerrainMaterial.SOIL: 10,
    TerrainMaterial.STONE: 30,
    TerrainMaterial.BEDROCK: 0
}



class Terrain(object):
    def __init__(self, map: TerrainMap, config: Dict[str, Any]) -> None:
        self.config = config
        self.width: int = config.get("display", {}).get("width", 1280)
        self.height: int = config.get("display", {}).get("height", 720)
        self.logic_grid = np.full((self.width, self.height), TerrainMaterial.EMPTY.value, dtype=np.uint8)
        self._display_grid = np.zeros((self.width, self.height), dtype=np.uint8) 
        self._generate_terrain(map)
        
        self.terrain_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.terrain_surface.fill((0,0,0,0))
        self.needs_surface_update = True
        self._update_surface() 


    def _generate_terrain(self, map: TerrainMap) -> None:
        if map == TerrainMap.FLAT:
            GRASS_THICKNESS = 10
            SOIL_THICKNESS = self.height // 3
            BEDROCK_THICKNESS = 10
            grass_start = self.height - (GRASS_THICKNESS + SOIL_THICKNESS + BEDROCK_THICKNESS)
            soil_start = self.height - (SOIL_THICKNESS + BEDROCK_THICKNESS)
            bedrock_start = self.height - BEDROCK_THICKNESS
            self.logic_grid[:, bedrock_start:self.height] = TerrainMaterial.BEDROCK.value
            self.logic_grid[:, soil_start:bedrock_start] = TerrainMaterial.SOIL.value
            self.logic_grid[:, grass_start:soil_start] = TerrainMaterial.GRASS.value
        else:
            raise ValueError(f"Unknown terrain map: {map}")


    def destroy_terrain(self, gradient_origin: Tuple[int, int], damage_gradient: np.ndarray) -> None:
        start_x, start_y = gradient_origin
        grad_width, grad_height = damage_gradient.shape
        end_x = start_x + grad_width
        end_y = start_y + grad_height
        clamp_start_x = max(0, start_x)
        clamp_start_y = max(0, start_y)
        clamp_end_x = min(self.width, end_x)
        clamp_end_y = min(self.height, end_y)
        if clamp_start_x >= clamp_end_x or clamp_start_y >= clamp_end_y:
            return
        grid_slice_x = slice(clamp_start_x, clamp_end_x)
        grid_slice_y = slice(clamp_start_y, clamp_end_y)
        grad_slice_x = slice(clamp_start_x - start_x, clamp_end_x - start_x)
        grad_slice_y = slice(clamp_start_y - start_y, clamp_end_y - start_y)
        target_grid_area = self.logic_grid[grid_slice_x, grid_slice_y]
        relevant_damage = damage_gradient[grad_slice_x, grad_slice_y]
        if target_grid_area.shape != relevant_damage.shape:
             print(f"Shape mismatch error in destroy_terrain: Grid {target_grid_area.shape}, Damage {relevant_damage.shape}")
             return
        vulnerable_mask = (target_grid_area != TerrainMaterial.EMPTY.value) & \
                          (target_grid_area != TerrainMaterial.BEDROCK.value)
        if not np.any(vulnerable_mask):
            return
        hardness_values = np.vectorize(lambda mat_val: MATERIAL_HARDNESS.get(TerrainMaterial(mat_val), 255))(target_grid_area)
        damage_over_hardness_mask = (relevant_damage > hardness_values)
        final_destroy_mask = damage_over_hardness_mask & vulnerable_mask
        if np.any(final_destroy_mask):
            target_grid_area[final_destroy_mask] = TerrainMaterial.EMPTY.value
            self.needs_surface_update = True


    def _update_surface(self):
        if not self.needs_surface_update:
            return
        changed_mask = self.logic_grid != self._display_grid
        changed_coords = np.argwhere(changed_mask)
        if changed_coords.size > 0:
            for x, y in changed_coords:
                new_material_value = self.logic_grid[x, y]
                color = MATERIAL_COLOR.get(TerrainMaterial(new_material_value), (0,0,0,0))
                self.terrain_surface.set_at((x, y), color)
            self._display_grid = self.logic_grid.copy()
        self.needs_surface_update = False


    def draw(self, screen: pygame.Surface) -> None:
        self._update_surface()
        screen.blit(self.terrain_surface, (0, 0))



    
