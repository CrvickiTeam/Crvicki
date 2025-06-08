import pygame
import numpy as np
from typing import Dict, Any, Tuple, List
from enum import Enum


class TerrainMaterial(Enum):
    EMPTY = 0
    GRASS = 1
    SOIL = 2
    STONE = 3
    BEDROCK = 4

class TerrainMap(Enum):
    FLAT = 0
    HILL = 1

DEFAULT_MATERIAL_CONFIG = [
    {
        "_type": "EMPTY",
        "color": [0, 0, 0, 0],
        "hardness": 0
    },
    {
        "_type": "GRASS",
        "color": [0, 255, 0, 255],
        "hardness": 10
    },
    {
        "_type": "SOIL",
        "color": [139, 69, 19, 255],
        "hardness": 10
    },
    {
        "_type": "STONE",
        "color": [128, 128, 128, 255],
        "hardness": 30
    },
    {
        "_type": "BEDROCK",
        "color": [105, 105, 105, 255],
        "hardness": 0
    }
]


def material_config_to_array(materials_config: List[Dict[str, Any]]) -> Tuple[np.ndarray, np.ndarray]:
    material_colors = np.zeros((len(TerrainMaterial), 4), dtype=np.uint8)
    material_hardnesses = np.zeros(len(TerrainMaterial), dtype=np.uint8)
    try:
        if len(materials_config) != len(TerrainMaterial):
            raise ValueError("Mismatch between materials_config and TerrainMaterial enum length.")
        for i in range(len(materials_config)):
            material = materials_config[i]
            material_name = material.get("_type")
            if material_name != TerrainMaterial(i).name:
                raise ValueError(f"Material name mismatch: {material_name} != {TerrainMaterial(i).name}")
            color = material.get("color", None)
            hardness = material.get("hardness", None)
            if color is None or hardness is None:
                raise ValueError(f"Missing color or hardness for material {material_name}.")
            material_colors[i] = np.array(color, dtype=np.uint8)
            material_hardnesses[i] = hardness
        return material_colors, material_hardnesses
    except Exception as e:
        print(f"Error converting material config to array: {e}\nSwitching to default materials.")
        for i in range(len(DEFAULT_MATERIAL_CONFIG)):
            material = DEFAULT_MATERIAL_CONFIG[i]
            color = material.get("color", None)
            hardness = material.get("hardness", None)
            if color is None or hardness is None:
                raise ValueError(f"Missing color or hardness for default material {i}.")
            material_colors[i] = np.array(color, dtype=np.uint8)
            material_hardnesses[i] = hardness
        return material_colors, material_hardnesses


class Terrain(object):
    def __init__(self, map: TerrainMap, config: Dict[str, Any]) -> None:
        self.config = config
        display_config: dict = config.get("display", {})
        terrain_config: dict = config.get("game", {}).get("terrain", {})
        materials_config: List[Dict[str, Any]] = terrain_config.get("materials", DEFAULT_MATERIAL_CONFIG) # Use default if missing
        self.width: int = display_config.get("width", 1280)
        self.height: int = display_config.get("height", 720)
        self.material_colors, self.material_hardnesses = material_config_to_array(materials_config)

        self.logic_grid = np.full((self.width, self.height), TerrainMaterial.EMPTY.value, dtype=np.uint8)
        self._display_grid = np.full((self.width, self.height), TerrainMaterial.EMPTY.value, dtype=np.uint8)
        self._generate_terrain(map)

        self.terrain_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.terrain_surface.fill((0,0,0,0))
        self.needs_surface_update = True
        self._update_surface()


    def _generate_terrain(self, map: TerrainMap) -> None:
        if map == TerrainMap.FLAT:
            terrain_gen_cfg = self.config.get("game", {}).get("terrain", {})
            GRASS_THICKNESS = terrain_gen_cfg.get("grass_thickness", 10)
            soil_ratio = terrain_gen_cfg.get("soil_thickness_ratio")
            if soil_ratio is not None:
                SOIL_THICKNESS = int(self.height * soil_ratio)
            else:
                SOIL_THICKNESS = self.height // 3
            BEDROCK_THICKNESS = terrain_gen_cfg.get("bedrock_thickness", 10)

            grass_start = self.height - (GRASS_THICKNESS + SOIL_THICKNESS + BEDROCK_THICKNESS)
            soil_start = self.height - (SOIL_THICKNESS + BEDROCK_THICKNESS)
            bedrock_start = self.height - BEDROCK_THICKNESS

            grass_start = max(0, grass_start)
            soil_start = max(0, soil_start)
            bedrock_start = max(0, bedrock_start)

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

        hardness_values = self.material_hardnesses[target_grid_area]
        bedrock_value = TerrainMaterial.BEDROCK.value
        bedrock_hardness = self.material_hardnesses[bedrock_value]

        if bedrock_hardness == 0:
             vulnerable_mask = (target_grid_area != TerrainMaterial.EMPTY.value) & \
                               (target_grid_area != bedrock_value)
        else:
             vulnerable_mask = (target_grid_area != TerrainMaterial.EMPTY.value) & \
                               (hardness_values > 0)

        if not np.any(vulnerable_mask):
            return

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
                color = self.material_colors[new_material_value]
                self.terrain_surface.set_at((x, y), tuple(color))
            self._display_grid = self.logic_grid.copy()
        self.needs_surface_update = False


    def draw(self, screen: pygame.Surface) -> None:
        self._update_surface()
        screen.blit(self.terrain_surface, (0, 0))