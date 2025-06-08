import pygame
import numpy as np
from typing import Dict, Any, Tuple, List
from enum import Enum
import random


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
    def __init__(self, map_type: TerrainMap, config: Dict[str, Any]) -> None: # Changed 'map' to 'map_type'
        self.config = config
        display_config: dict = config.get("display", {})
        
        # Get the general terrain config first
        terrain_config_base: dict = config.get("game", {}).get("terrain", {})
        materials_config: List[Dict[str, Any]] = terrain_config_base.get("materials", DEFAULT_MATERIAL_CONFIG)
        
        # Get map-specific config
        map_configs: dict = terrain_config_base.get("maps", {})
        if map_type == TerrainMap.FLAT:
            self.map_specific_config = map_configs.get("flat", {})
        elif map_type == TerrainMap.HILL:
            self.map_specific_config = map_configs.get("hill", {})
        else:
            self.map_specific_config = {} # Default to empty if map type unknown or not configured

        self.width: int = display_config.get("width", 1280)
        self.height: int = display_config.get("height", 720)
        self.material_colors, self.material_hardnesses = material_config_to_array(materials_config)

        self.logic_grid = np.full((self.width, self.height), TerrainMaterial.EMPTY.value, dtype=np.uint8)
        self._display_grid = np.full((self.width, self.height), TerrainMaterial.EMPTY.value, dtype=np.uint8)
        self._generate_terrain(map_type)

        self.terrain_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.terrain_surface.fill((0,0,0,0))
        self.needs_surface_update = True
        self._update_surface()


    def _generate_terrain(self, map_type: TerrainMap) -> None:
        # Use map_specific_config for generation parameters
        GRASS_THICKNESS = self.map_specific_config.get("grass_thickness", 10)
        soil_ratio = self.map_specific_config.get("soil_thickness_ratio", 0.333)
        SOIL_THICKNESS = int(self.height * soil_ratio)
        BEDROCK_THICKNESS = self.map_specific_config.get("bedrock_thickness", 10)

        bedrock_start_y = self.height - BEDROCK_THICKNESS
        soil_start_y = bedrock_start_y - SOIL_THICKNESS
        grass_start_y = soil_start_y - GRASS_THICKNESS

        bedrock_start_y = max(0, min(self.height, bedrock_start_y))
        soil_start_y = max(0, min(bedrock_start_y, soil_start_y))
        grass_start_y = max(0, min(soil_start_y, grass_start_y))

        if bedrock_start_y < self.height:
            self.logic_grid[:, bedrock_start_y:self.height] = TerrainMaterial.BEDROCK.value
        if soil_start_y < bedrock_start_y:
            self.logic_grid[:, soil_start_y:bedrock_start_y] = TerrainMaterial.SOIL.value

        if map_type == TerrainMap.FLAT:
            if grass_start_y < soil_start_y:
                self.logic_grid[:, grass_start_y:soil_start_y] = TerrainMaterial.GRASS.value
        
        elif map_type == TerrainMap.HILL:
            if grass_start_y < soil_start_y:
                self.logic_grid[:, grass_start_y:soil_start_y] = TerrainMaterial.GRASS.value

            hill_center_x = self.width // 2
            hill_width_ratio = self.map_specific_config.get("hill_width_ratio", 0.4) 
            hill_width_at_base = int(self.width * hill_width_ratio)
            
            hill_peak_soil_elevation_ratio = self.map_specific_config.get("hill_peak_elevation_ratio", 0.2) 
            hill_peak_soil_elevation = int(self.height * hill_peak_soil_elevation_ratio)
            
            base_soil_surface_y = soil_start_y 
            hill_half_width = hill_width_at_base / 2.0

            if hill_half_width > 0:
                for x_coord in range(self.width):
                    dx_from_hill_center = abs(x_coord - hill_center_x)
                    if dx_from_hill_center < hill_half_width:
                        parabolic_factor = 1.0 - (dx_from_hill_center / hill_half_width)**2
                        current_hill_soil_elevation = hill_peak_soil_elevation * parabolic_factor
                        
                        hill_soil_top_y = int(base_soil_surface_y - current_hill_soil_elevation)
                        hill_soil_top_y = max(0, min(base_soil_surface_y, hill_soil_top_y))

                        hill_grass_top_y = int(hill_soil_top_y - GRASS_THICKNESS)
                        hill_grass_top_y = max(0, min(hill_soil_top_y, hill_grass_top_y))

                        if hill_soil_top_y < base_soil_surface_y:
                            self.logic_grid[x_coord, hill_soil_top_y:base_soil_surface_y] = TerrainMaterial.SOIL.value
                        if hill_grass_top_y < hill_soil_top_y:
                            self.logic_grid[x_coord, hill_grass_top_y:hill_soil_top_y] = TerrainMaterial.GRASS.value

            # Complex Stone Chunk Generation for HILL map
            num_stone_chunks = self.map_specific_config.get("stone_chunk_count", 5)
            main_radius_min = self.map_specific_config.get("stone_main_radius_min", 8)
            main_radius_max = self.map_specific_config.get("stone_main_radius_max", 15)
            blob_count_min = self.map_specific_config.get("stone_blob_count_min", 3)
            blob_count_max = self.map_specific_config.get("stone_blob_count_max", 6)
            blob_radius_min = self.map_specific_config.get("stone_blob_radius_min", 3)
            blob_radius_max = self.map_specific_config.get("stone_blob_radius_max", 7)
            blob_offset_factor = self.map_specific_config.get("stone_blob_offset_factor", 0.6)

            # Removed hill_base_start_x and hill_base_end_x for stone placement,
            # as stones will now be placed across the entire map width.

            for _ in range(num_stone_chunks):
                main_rock_radius = random.randint(main_radius_min, main_radius_max)
                # Pick a center x for the main rock across the entire map width
                cx_main = random.randint(0, self.width - 1)
                
                # Find a suitable y for the main rock center (e.g., within a soil layer)
                soil_indices_in_col = np.where(self.logic_grid[cx_main, :] == TerrainMaterial.SOIL.value)[0]
                if not soil_indices_in_col.size > 0:
                    # Fallback if no soil found at cx_main, try to place it deeper
                    # Ensure grass_start_y and bedrock_start_y are defined before this point
                    # (they are, from the general layer generation)
                    cy_main = random.randint(grass_start_y + GRASS_THICKNESS, bedrock_start_y - main_rock_radius)
                    cy_main = max(main_rock_radius, min(self.height - main_rock_radius -1, cy_main))
                else:
                    cy_main = random.choice(soil_indices_in_col)
                    # Ensure it's not too close to the surface or bedrock if possible
                    cy_main = max(main_rock_radius, min(self.height - main_rock_radius -1, cy_main))

                num_blobs = random.randint(blob_count_min, blob_count_max)
                for _ in range(num_blobs):
                    blob_r = random.randint(blob_radius_min, blob_radius_max)
                    
                    # Offset blob center from main rock center
                    angle = random.uniform(0, 2 * np.pi)
                    offset_dist = random.uniform(0, main_rock_radius * blob_offset_factor)
                    cx_blob = int(cx_main + offset_dist * np.cos(angle))
                    cy_blob = int(cy_main + offset_dist * np.sin(angle))

                    # Create the circular blob
                    for px_offset in range(-blob_r, blob_r + 1):
                        for py_offset in range(-blob_r, blob_r + 1):
                            if px_offset**2 + py_offset**2 <= blob_r**2: # Check if inside circle
                                px, py = cx_blob + px_offset, cy_blob + py_offset
                                
                                if 0 <= px < self.width and 0 <= py < self.height:
                                    current_material = self.logic_grid[px, py]
                                    # Place stone if the target is soil or grass (don't overwrite bedrock or other stones easily)
                                    if current_material == TerrainMaterial.SOIL.value or \
                                       current_material == TerrainMaterial.GRASS.value:
                                        self.logic_grid[px, py] = TerrainMaterial.STONE.value
        else:
            raise ValueError(f"Unknown terrain map_type: {map_type}")

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