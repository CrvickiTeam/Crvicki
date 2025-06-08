from typing import TYPE_CHECKING, Tuple, Optional, List, Dict, Any 
import pygame
import os
import math
import numpy as np
from enum import Enum

from .terrain import Terrain, TerrainMaterial
from .weapons.weapon import WeaponType, WEAPON_TYPES_ORDERED

if TYPE_CHECKING:
    from .game_manager import GameManager 

class PlayerTeam(Enum):
    TEAM_1 = 1
    TEAM_2 = 2

class Player:

    def __init__(self, start_pos: tuple[int, int], team: PlayerTeam, config: Dict[str, Any], game_manager: 'GameManager') -> None:
        self.config: Dict[str, Any] = config
        self.team: PlayerTeam = team
        self.game_manager: 'GameManager' = game_manager 
        self.alive: bool = True
        
        self.x: float = float(start_pos[0]) # Circle center x
        self.y: float = float(start_pos[1]) # Circle center y
        self.angle: float = 0.0 
        
        self.direction: int = 1 
        self.aim_angle: float = 45.0 

        player_cfg: Dict[str, Any] = self.config.get("game", {}).get("player", {})
        movement_cfg: Dict[str, Any] = player_cfg.get("movement", {})
        hitbox_cfg: Dict[str, Any] = player_cfg.get("hitbox", {})
        aiming_cfg: Dict[str, Any] = player_cfg.get("aiming", {})

        self.speed: float = float(movement_cfg.get("drive_speed", 100.0))
        self.gravity: float = float(movement_cfg.get("gravity", 400.0))
        self.max_step_height: int = int(movement_cfg.get("step_height", 5))
        self.max_move_distance_per_turn: float = float(movement_cfg.get("max_move_distance_per_turn", 150.0)) 
        self.health: int = int(player_cfg.get("max_health", 100))

        # Load radius for circular hitbox
        self.radius: float = float(hitbox_cfg.get("radius", 10.0)) # Default to 10 if not in config
        
        # self.width and self.height will now represent the diameter for the bounding box and sprite scaling
        self.width: int = int(self.radius * 2)
        self.height: int = int(self.radius * 2)


        self.aim_angle_rate: float = float(aiming_cfg.get("angle_change_rate", 60.0))
        self.aim_power_rate: float = float(aiming_cfg.get("power_change_rate", 50.0))
        self.min_aim_power: float = float(aiming_cfg.get("min_power", 10.0))
        self.max_aim_power: float = float(aiming_cfg.get("max_power", 135.0))
        self.default_aim_power: float = float(aiming_cfg.get("default_power", 50.0))
        self.aim_power: float = self.default_aim_power

        self.aim_max_up_degrees: float = float(aiming_cfg.get("max_up_degrees", 90.0)) 
        self.aim_min_down_degrees_offset: float = float(aiming_cfg.get("min_down_degrees_offset", -10.0)) 


        self.vx: float = 0.0
        self.vy: float = 0.0
        self.is_grounded: bool = False
        self.is_moving: bool = False 
        self.distance_moved_this_turn: float = 0.0 
        
        self.inventory: Dict[WeaponType, int] = {}
        self.selected_weapon_type: WeaponType = WeaponType.SMALL_BOMB 
        self._initialize_inventory()

        self.active_tank_image_orig: Optional[pygame.Surface] = None
        self.waiting_tank_image_orig: Optional[pygame.Surface] = None
        self.pipe_image_orig: Optional[pygame.Surface] = None
        self.load_sprites() # Sprites will be scaled to self.width, self.height (diameter)

        # self.rect is the bounding box of the circle
        self.rect: pygame.Rect = pygame.Rect(self.x - self.radius, self.y - self.radius, self.width, self.height)

        # Damage indicators
        self.damage_indicators: List[Dict[str, Any]] = []
        self.damage_font = pygame.font.Font(None, 28) # Font for damage numbers
        self.damage_text_color = (255, 50, 50) # Red color for damage
        self.damage_indicator_lifetime_ms = 1200 # How long the damage number stays (in ms)
        self.damage_indicator_float_speed_y = -30 # Pixels per second upwards


    def _initialize_inventory(self) -> None:
        """Sets up the initial weapon counts for the player from config."""
        player_config: Dict[str, Any] = self.config.get("game", {}).get("player", {})
        inventory_config: Dict[str, int] = player_config.get("initial_inventory", {})
        
        self.inventory = {}
        
        # Iterate through all defined weapon types to ensure they are in the inventory
        for weapon_type_enum_member in WeaponType:
            weapon_name_str = weapon_type_enum_member.name # e.g., "SMALL_BOMB"
            # Get quantity from config, default to 0 if not specified for this weapon type
            quantity = inventory_config.get(weapon_name_str, 0) 
            self.inventory[weapon_type_enum_member] = quantity
            
        # Ensure the default selected weapon is valid or fallback
        if self.get_weapon_quantity(self.selected_weapon_type) == 0 and self.selected_weapon_type != WeaponType.SMALL_BOMB:
             # If selected weapon has 0 ammo and isn't infinite small bomb, try to select small bomb
            if self.get_weapon_quantity(WeaponType.SMALL_BOMB) != 0:
                self.selected_weapon_type = WeaponType.SMALL_BOMB
            else: # Fallback to first available weapon if small bomb also has 0 (unlikely with -1 default)
                for wt in WEAPON_TYPES_ORDERED:
                    if self.get_weapon_quantity(wt) != 0:
                        self.selected_weapon_type = wt
                        break
        
        print(f"Player {self.team.name} initialized inventory: {self.inventory}")

    def get_selected_weapon_type(self) -> WeaponType:
        return self.selected_weapon_type

    def get_weapon_quantity(self, weapon_type: WeaponType) -> int:
        return self.inventory.get(weapon_type, 0)

    def get_weapon_quantity_display(self, weapon_type: WeaponType) -> str:
        quantity = self.inventory.get(weapon_type, 0)
        return "Inf" if quantity == -1 else str(quantity)

    def select_weapon_by_index(self, index: int) -> bool:
        """Selects a weapon by its order in WEAPON_TYPES_ORDERED. Returns True if selection changed."""
        if 0 <= index < len(WEAPON_TYPES_ORDERED):
            target_weapon = WEAPON_TYPES_ORDERED[index]
            quantity = self.get_weapon_quantity(target_weapon)
            if quantity != 0: # Can select if infinite (-1) or has ammo (>0)
                if self.selected_weapon_type != target_weapon:
                    self.selected_weapon_type = target_weapon
                    print(f"Player {self.team.name} selected {target_weapon.display_name()}")
                    return True
        return False
    
    def consume_selected_weapon(self) -> bool:
        """Decrements the count of the selected weapon if it's not infinite and has ammo. Returns True if weapon can be fired."""
        quantity = self.get_weapon_quantity(self.selected_weapon_type)
        if quantity == -1: # Infinite
            return True
        if quantity > 0:
            self.inventory[self.selected_weapon_type] -= 1
            print(f"{self.selected_weapon_type.display_name()} consumed. Remaining: {self.inventory[self.selected_weapon_type]}")
            return True
        print(f"Cannot fire {self.selected_weapon_type.display_name()}, no ammo.")
        return False # No ammo

    def reset_turn_state(self) -> None:
        """Resets player's state at the beginning of their turn."""
        self.distance_moved_this_turn = 0.0
        self.is_moving = False 
        self.vx = 0 # Stop horizontal movement from previous turn/physics
        
        # Default to SMALL_BOMB at the start of the turn
        self.selected_weapon_type = WeaponType.SMALL_BOMB
        
        # Optional: Add a check to ensure Small Bomb is actually available,
        # though with infinite Small Bombs, this is less critical.
        # If Small Bomb somehow had 0 ammo, you might want to select the first available weapon.
        if self.get_weapon_quantity(WeaponType.SMALL_BOMB) == 0:
            # Fallback to the first available weapon in order if Small Bomb is (unexpectedly) out
            for wt in WEAPON_TYPES_ORDERED:
                if self.get_weapon_quantity(wt) != 0: # != 0 means > 0 or -1 (infinite)
                    self.selected_weapon_type = wt
                    break
        
        print(f"Player {self.team.name} turn reset. Selected weapon: {self.selected_weapon_type.display_name()}")


    def load_sprites(self) -> None:
        script_dir = os.path.dirname(__file__)
        project_root = os.path.abspath(os.path.join(script_dir, "..", ".."))
        base_path = os.path.join(project_root, "assets", "graphics", "characters")

        try:
            self.active_tank_image_orig = pygame.image.load(
                os.path.join(base_path, "GREEN-01ORIGINAL-TANK.png")).convert_alpha()
            self.waiting_tank_image_orig = pygame.image.load(
                os.path.join(base_path, "GREEN-02OPEN-WORM-HAT-TANK.png")).convert_alpha()
            self.pipe_image_orig = pygame.image.load(os.path.join(base_path, "TANK-PIPE.png")).convert_alpha()

            # Scale sprites to the diameter
            if self.active_tank_image_orig:
                self.active_tank_image_orig = pygame.transform.scale(self.active_tank_image_orig, (self.width, self.height))
            if self.waiting_tank_image_orig:
                self.waiting_tank_image_orig = pygame.transform.scale(self.waiting_tank_image_orig, (self.width, self.height))
            # Pipe scaling might be different or handled in draw

        except pygame.error as e:
            print(f"Error loading player sprites: {e}")
            try:
                placeholder_path = os.path.join(project_root, "assets", "graphics",
                                                "missing.png") 
                placeholder_img = pygame.image.load(placeholder_path).convert_alpha()
                ph_width = self.width # Diameter
                ph_height = self.height # Diameter

                if self.active_tank_image_orig is None:
                    self.active_tank_image_orig = pygame.transform.scale(placeholder_img, (ph_width, ph_height))
                if self.waiting_tank_image_orig is None:
                    self.waiting_tank_image_orig = pygame.transform.scale(placeholder_img, (ph_width, ph_height))
                if self.pipe_image_orig is None:
                    self.pipe_image_orig = pygame.transform.scale(placeholder_img, (
                    max(1, ph_width // 2), max(1, ph_height // 4))) 
            except pygame.error as e_miss:
                print(f"Error loading placeholder sprite: {e_miss}")
                ph_width = self.width
                ph_height = self.height
                fallback_surface = pygame.Surface((ph_width, ph_height), pygame.SRCALPHA)
                fallback_surface.fill((255, 0, 255, 128))
                if self.active_tank_image_orig is None: self.active_tank_image_orig = fallback_surface
                if self.waiting_tank_image_orig is None: self.waiting_tank_image_orig = fallback_surface.copy()
                if self.pipe_image_orig is None:
                    self.pipe_image_orig = pygame.Surface((max(1, ph_width // 2), max(1, ph_height // 4)),
                                                          pygame.SRCALPHA) 
                    self.pipe_image_orig.fill((255, 0, 255, 128))


    def move_left(self) -> None:
        old_direction = self.direction
        self.direction = -1

        if old_direction != self.direction: 
            self.aim_angle = 180.0 - self.aim_angle
            
        if self.distance_moved_this_turn < self.max_move_distance_per_turn:
            self.is_moving = True
            self.vx = -self.speed
        else:
            self.vx = 0
            self.is_moving = False 

    def move_right(self) -> None:
        old_direction = self.direction
        self.direction = 1

        if old_direction != self.direction: 
            self.aim_angle = 180.0 - self.aim_angle
            
        if self.distance_moved_this_turn < self.max_move_distance_per_turn:
            self.is_moving = True
            self.vx = self.speed
        else:
            self.vx = 0
            self.is_moving = False

    def stop_moving(self) -> None:
        self.is_moving = False
        self.vx = 0.0

    def aim_up(self, dt: float) -> None:
        if self.direction == 1: 
            self.aim_angle += self.aim_angle_rate * dt 
            self.aim_angle = min(self.aim_angle, self.aim_max_up_degrees) 
        else: 
            self.aim_angle -= self.aim_angle_rate * dt 
            self.aim_angle = max(self.aim_angle, self.aim_max_up_degrees) 

    def aim_down(self, dt: float) -> None:
        if self.direction == 1: 
            self.aim_angle -= self.aim_angle_rate * dt 
            self.aim_angle = max(self.aim_angle, self.aim_min_down_degrees_offset) 
        else: 
            self.aim_angle += self.aim_angle_rate * dt 
            max_down_angle_left_facing = 180.0 - self.aim_min_down_degrees_offset 
            self.aim_angle = min(self.aim_angle, max_down_angle_left_facing)

    def increase_power(self, dt: float) -> None:
        self.aim_power += self.aim_power_rate * dt 
        self.aim_power = min(self.aim_power, self.max_aim_power) 

    def decrease_power(self, dt: float) -> None:
        self.aim_power -= self.aim_power_rate * dt 
        self.aim_power = max(self.aim_power, self.min_aim_power) 

    def get_shot_info(self) -> tuple[float, float]:
        """Returns the current aim angle (degrees) and power."""
        return self.aim_angle, self.aim_power

    # --- New Collision Check for Circle ---
    def _check_terrain_collision_circle(self, cx: float, cy: float, terrain: Terrain) -> bool:
        # Bounding box of the circle in grid coordinates
        min_gx = max(0, int(cx - self.radius))
        max_gx = min(terrain.width - 1, int(cx + self.radius))
        min_gy = max(0, int(cy - self.radius))
        max_gy = min(terrain.height - 1, int(cy + self.radius))

        radius_sq = self.radius * self.radius

        for gx in range(min_gx, max_gx + 1):
            for gy in range(min_gy, max_gy + 1):
                if terrain.logic_grid[gx, gy] != TerrainMaterial.EMPTY.value:
                    # Cell is solid. Check distance from circle center to closest point on this grid cell.
                    # Cell corners are (gx, gy), (gx+1, gy), (gx, gy+1), (gx+1, gy+1)
                    closest_x = max(float(gx), min(cx, float(gx + 1.0))) # Cell is 1x1 unit
                    closest_y = max(float(gy), min(cy, float(gy + 1.0))) # Cell is 1x1 unit

                    dist_sq = (cx - closest_x)**2 + (cy - closest_y)**2
                    
                    if dist_sq < radius_sq: # Using < for slight tolerance
                        return True
        return False

    # --- Update ---
    def update(self, dt: float, terrain: Terrain) -> None:
        if not self.alive or terrain is None: return

        x_at_start_of_frame: float = self.x 
        y_at_start_of_frame: float = self.y

        # Horizontal Movement
        if self.is_moving:
            potential_dx: float = self.vx * dt 
            remaining_fuel: float = self.max_move_distance_per_turn - self.distance_moved_this_turn
            dx_to_apply_this_frame: float

            if remaining_fuel <= 0:
                dx_to_apply_this_frame = 0.0
                self.stop_moving()
            elif abs(potential_dx) > remaining_fuel:
                dx_to_apply_this_frame = math.copysign(remaining_fuel, potential_dx)
            else:
                dx_to_apply_this_frame = potential_dx
            
            if dx_to_apply_this_frame == 0.0 and self.vx != 0.0:
                self.stop_moving()

            target_x: float = self.x + dx_to_apply_this_frame
            
            final_x_after_horizontal_pass: float = target_x
            
            # Boundary checks for x
            blocked_by_boundary_x = False
            if target_x - self.radius < 0:
                final_x_after_horizontal_pass = self.radius
                blocked_by_boundary_x = True
            elif target_x + self.radius > terrain.width:
                final_x_after_horizontal_pass = terrain.width - self.radius
                blocked_by_boundary_x = True
            
            original_y_before_step_attempt: float = self.y
            collided_horizontally = False
            if not blocked_by_boundary_x and self._check_terrain_collision_circle(final_x_after_horizontal_pass, self.y, terrain):
                collided_horizontally = True
                stepped_up: bool = False
                for step in range(1, self.max_step_height + 1):
                    if not self._check_terrain_collision_circle(final_x_after_horizontal_pass, self.y - step, terrain):
                        self.y -= step 
                        stepped_up = True
                        self.is_grounded = True 
                        self.vy = 0            
                        collided_horizontally = False # No longer considered a horizontal collision if we stepped
                        break 
                if not stepped_up:
                    final_x_after_horizontal_pass = x_at_start_of_frame 
                    self.y = original_y_before_step_attempt 
            
            self.x = final_x_after_horizontal_pass
            
            actual_horizontal_displacement_this_frame: float = abs(self.x - x_at_start_of_frame)
            self.distance_moved_this_turn += actual_horizontal_displacement_this_frame

            if self.distance_moved_this_turn >= self.max_move_distance_per_turn:
                self.distance_moved_this_turn = self.max_move_distance_per_turn
                if self.is_moving: 
                    self.stop_moving()
        
        # Vertical Movement (Gravity)
        if not self.is_grounded:
            self.vy += self.gravity * dt
        else: 
            self.vy = 0 
        
        dy: float = self.vy * dt 
        target_y_gravity: float = self.y + dy
        
        new_is_grounded_this_frame = False

        # Boundary checks for y
        if target_y_gravity - self.radius < 0: # Hit ceiling
            self.y = self.radius
            self.vy = 0 
            new_is_grounded_this_frame = False
        elif target_y_gravity + self.radius > terrain.height: # Hit bottom of world
            self.y = terrain.height - self.radius
            self.vy = 0
            new_is_grounded_this_frame = True
        else:
            # Terrain collision check for y
            if self._check_terrain_collision_circle(self.x, target_y_gravity, terrain):
                if dy >= 0: # Moving downwards or stationary and embedded
                    # Iteratively move up until no collision
                    test_y = target_y_gravity
                    while self._check_terrain_collision_circle(self.x, test_y, terrain):
                        test_y -= 1.0 # Move up by 1 pixel
                        if test_y < self.y - self.radius - self.height: break # Safety break
                    self.y = test_y + 1.0 # Place just above the collision point
                    self.vy = 0
                    new_is_grounded_this_frame = True
                elif dy < 0: # Moving upwards and hit something
                    test_y = target_y_gravity
                    while self._check_terrain_collision_circle(self.x, test_y, terrain):
                        test_y += 1.0 # Move down by 1 pixel
                        if test_y > self.y + self.radius + self.height: break # Safety
                    self.y = test_y - 1.0 # Place just below
                    self.vy = 0 
                    new_is_grounded_this_frame = False 
            else: # No collision with terrain at target_y_gravity: potentially airborne
                self.y = target_y_gravity
                # Sticky Feet / Downward Probe
                if dy >= 0: 
                    if self._check_terrain_collision_circle(self.x, self.y + 1, terrain): # Check 1 pixel below
                        test_y = self.y + 1
                        while self._check_terrain_collision_circle(self.x, test_y, terrain):
                            test_y -= 1.0
                            if test_y < self.y - self.radius - self.height: break
                        self.y = test_y + 1.0
                        self.vy = 0
                        new_is_grounded_this_frame = True
                    else:
                        new_is_grounded_this_frame = False
                else: 
                    new_is_grounded_this_frame = False

        self.is_grounded = new_is_grounded_this_frame

        # Angle Calculation
        if self.is_grounded:
            # Sample points slightly offset horizontally from center, at bottom of circle
            # The old method used self.width // 4, which is self.radius / 2
            offset_for_angle_calc = self.radius * 0.5 
            left_x_angle: int = max(0, int(self.x - offset_for_angle_calc))
            right_x_angle: int = min(terrain.width - 1, int(self.x + offset_for_angle_calc))
            
            # Find ground y under these points
            # Start scan from bottom of circle and go up/down a bit
            base_scan_y = int(self.y + self.radius) 
            scan_range_y_angle: int = self.max_step_height + int(self.radius / 2) + 2

            left_y_angle: int = base_scan_y
            for y_offset in range(-scan_range_y_angle, scan_range_y_angle + 1):
                y_check = min(terrain.height - 1, max(0, base_scan_y + y_offset))
                if terrain.logic_grid[left_x_angle, y_check] != TerrainMaterial.EMPTY.value:
                    # Found solid ground, now find the top-most solid pixel for this x
                    temp_y = y_check
                    while temp_y > 0 and terrain.logic_grid[left_x_angle, temp_y -1] != TerrainMaterial.EMPTY.value:
                        temp_y -=1
                    left_y_angle = temp_y
                    break
            
            right_y_angle: int = base_scan_y
            for y_offset in range(-scan_range_y_angle, scan_range_y_angle + 1):
                y_check = min(terrain.height - 1, max(0, base_scan_y + y_offset))
                if terrain.logic_grid[right_x_angle, y_check] != TerrainMaterial.EMPTY.value:
                    temp_y = y_check
                    while temp_y > 0 and terrain.logic_grid[right_x_angle, temp_y -1] != TerrainMaterial.EMPTY.value:
                        temp_y -=1
                    right_y_angle = temp_y
                    break
            
            delta_x_val_angle: float = float(right_x_angle - left_x_angle)
            delta_y_val_angle: float = float(right_y_angle - left_y_angle)
            if delta_x_val_angle != 0:
                self.angle = -math.degrees(math.atan2(delta_y_val_angle, delta_x_val_angle))
            else:
                self.angle = 0.0
        
        # Update bounding rect for drawing and broad-phase
        self.rect.left = int(self.x - self.radius)
        self.rect.top = int(self.y - self.radius)
        self.rect.width = int(self.radius * 2)
        self.rect.height = int(self.radius * 2)

        # --- Update Damage Indicators ---
        current_time_ms = pygame.time.get_ticks()
        for i in range(len(self.damage_indicators) - 1, -1, -1): # Iterate backwards for safe removal
            indicator = self.damage_indicators[i]
            
            # Update position (float upwards)
            indicator["position"][1] += indicator["float_speed_y"] * dt
            
            # Update alpha (fade out)
            age_ms = current_time_ms - indicator["creation_time_ms"]
            if age_ms >= indicator["lifetime_ms"]:
                self.damage_indicators.pop(i)
                continue
            
            # Quadratic fade for smoother end (alpha = 255 * (remaining_life_ratio)^2)
            remaining_life_ratio = 1.0 - (age_ms / indicator["lifetime_ms"])
            indicator["alpha"] = int(255 * remaining_life_ratio * remaining_life_ratio) 
            indicator["alpha"] = max(0, min(255, indicator["alpha"])) # Clamp alpha


    def draw(self, screen: pygame.Surface) -> None:
        if not self.alive:
            return

        is_active_player = (self.game_manager.get_active_player() == self)

        base_tank_sprite = self.active_tank_image_orig if is_active_player else self.waiting_tank_image_orig
        if base_tank_sprite:
            tank_surface_to_render = pygame.transform.flip(base_tank_sprite, True, False) if self.direction == -1 else base_tank_sprite
            rotated_tank_surface = pygame.transform.rotate(tank_surface_to_render, self.angle)
            tank_render_rect = rotated_tank_surface.get_rect(center=(int(self.x), int(self.y)))
            screen.blit(rotated_tank_surface, tank_render_rect.topleft)
        else:
            hitbox_color = (255, 0, 0) if self.team == PlayerTeam.TEAM_1 else (0, 0, 255)
            pygame.draw.circle(screen, hitbox_color, (int(self.x), int(self.y)), int(self.radius), 1)

        pipe_world_anchor_x, pipe_world_anchor_y = self.x, self.y

        if self.pipe_image_orig:
            player_local_pipe_mount_dx = 2.0 
            player_local_pipe_mount_dy = 5.0 
            pipe_pivot_local_x = 22 
            pipe_pivot_local_y = 25 

            mount_offset_vec = pygame.math.Vector2(player_local_pipe_mount_dx * self.direction, 
                                                   player_local_pipe_mount_dy)
            rotated_mount_offset = mount_offset_vec.rotate(self.angle) 
            pipe_world_anchor_x = self.x + rotated_mount_offset.x
            pipe_world_anchor_y = self.y + rotated_mount_offset.y
            
            current_pipe_image_to_rotate: pygame.Surface
            actual_pivot_x_on_pipe_image: float
            
            display_pipe_world_aim_angle: float
            if is_active_player:
                display_pipe_world_aim_angle = self.aim_angle
            else:
                if self.direction == 1: 
                    display_pipe_world_aim_angle = 0.0
                else: 
                    display_pipe_world_aim_angle = 180.0

            pygame_rotation_angle: float
            if self.direction == -1: 
                current_pipe_image_to_rotate = pygame.transform.flip(self.pipe_image_orig, True, False)
                actual_pivot_x_on_pipe_image = current_pipe_image_to_rotate.get_width() - pipe_pivot_local_x
                pygame_rotation_angle = display_pipe_world_aim_angle - 180.0
            else: 
                current_pipe_image_to_rotate = self.pipe_image_orig
                actual_pivot_x_on_pipe_image = float(pipe_pivot_local_x)
                pygame_rotation_angle = display_pipe_world_aim_angle

            pipe_image_rect = current_pipe_image_to_rotate.get_rect()
            pivot_offset_in_pipe_image = pygame.math.Vector2(actual_pivot_x_on_pipe_image - pipe_image_rect.centerx,
                                                             pipe_pivot_local_y - pipe_image_rect.centery)
            rotated_pipe_image = pygame.transform.rotate(current_pipe_image_to_rotate, pygame_rotation_angle)
            rotated_pivot_offset_in_pipe_image = pivot_offset_in_pipe_image.rotate(-pygame_rotation_angle)
            rotated_pipe_rect = rotated_pipe_image.get_rect()
            rotated_pipe_rect.center = (pipe_world_anchor_x - rotated_pivot_offset_in_pipe_image.x, 
                                        pipe_world_anchor_y - rotated_pivot_offset_in_pipe_image.y)
            
            screen.blit(rotated_pipe_image, rotated_pipe_rect.topleft)

        # --- Health Bar ---
        max_health_val = self.config.get("game", {}).get("player", {}).get("max_health", 100)
        bar_width_health = 40 
        bar_height_health = 6
        current_health_percentage = self.health / max_health_val if max_health_val > 0 else 0
        fill_health = current_health_percentage * bar_width_health
        bar_x_health = self.x - bar_width_health // 2
        bar_y_health = self.y - self.radius - 15 # Health bar above player
        
        bar_background_color = (220, 220, 220) # Lighter background color

        pygame.draw.rect(screen, bar_background_color, (bar_x_health, bar_y_health, bar_width_health, bar_height_health)) # Background
        pygame.draw.rect(screen, (255, 0, 0), (bar_x_health, bar_y_health, fill_health, bar_height_health)) # Health fill
        pygame.draw.rect(screen, (255, 255, 255), (bar_x_health, bar_y_health, bar_width_health, bar_height_health), 1) # Border

        if is_active_player: 
            # --- Aiming Line ---
            start_x_indicator, start_y_indicator = pipe_world_anchor_x, pipe_world_anchor_y 
            if self.pipe_image_orig:
                pipe_length_from_pivot = self.pipe_image_orig.get_width() - pipe_pivot_local_x 
                aim_rad_world = math.radians(self.aim_angle) 
                tip_offset_x = pipe_length_from_pivot * math.cos(aim_rad_world)
                tip_offset_y = -pipe_length_from_pivot * math.sin(aim_rad_world)
                start_x_indicator = pipe_world_anchor_x + tip_offset_x 
                start_y_indicator = pipe_world_anchor_y + tip_offset_y
            
            line_length = 30 + (self.aim_power / self.max_aim_power) * 70
            end_x_indicator = start_x_indicator + line_length * math.cos(math.radians(self.aim_angle))
            end_y_indicator = start_y_indicator - line_length * math.sin(math.radians(self.aim_angle))
            pygame.draw.line(screen, (255, 255, 255, 180), 
                             (int(start_x_indicator), int(start_y_indicator)), 
                             (int(end_x_indicator), int(end_y_indicator)), 2)
            
            # --- Fuel Bar (Movement Bar) ---
            bar_width_fuel = 40
            bar_height_fuel = 6
            remaining_fuel_percentage = 0.0
            if self.max_move_distance_per_turn > 0: 
                remaining_fuel_percentage = (self.max_move_distance_per_turn - self.distance_moved_this_turn) / self.max_move_distance_per_turn
            remaining_fuel_percentage = max(0.0, min(1.0, remaining_fuel_percentage)) 
            
            fill_fuel = remaining_fuel_percentage * bar_width_fuel
            
            bar_x_fuel = self.x - bar_width_fuel // 2
            bar_y_fuel = bar_y_health - bar_height_fuel - 2 

            pygame.draw.rect(screen, bar_background_color, (bar_x_fuel, bar_y_fuel, bar_width_fuel, bar_height_fuel)) # Background
            pygame.draw.rect(screen, (0, 0, 255), (bar_x_fuel, bar_y_fuel, fill_fuel, bar_height_fuel)) # Blue fill for fuel
            pygame.draw.rect(screen, (255, 255, 255), (bar_x_fuel, bar_y_fuel, bar_width_fuel, bar_height_fuel), 1) # Border

        # --- Draw Damage Indicators ---
        for indicator in self.damage_indicators:
            # Create a temporary surface for rendering with alpha
            # This is safer than modifying the original surface's alpha directly if it's reused
            temp_surface = indicator["surface"].copy() 
            temp_surface.set_alpha(indicator["alpha"])
            
            # Center the text surface at its current position
            text_rect = temp_surface.get_rect(center=(int(indicator["position"][0]), int(indicator["position"][1])))
            screen.blit(temp_surface, text_rect)

    def apply_damage(self, damage: int) -> None:
        if not self.alive or damage <= 0: # Only apply if damage is positive
            return
        
        actual_damage = int(damage) # Ensure it's an integer
        self.health -= actual_damage
        
        # --- Create Damage Indicator ---
        text = f"-{actual_damage}"
        text_surface = self.damage_font.render(text, True, self.damage_text_color)
        
        # Initial position slightly above the player's center
        # Randomize x slightly for multiple hits not overlapping perfectly
        start_x = self.x + np.random.uniform(-self.radius * 0.3, self.radius * 0.3) # Reduced random range
        start_y = self.y - self.radius - 15 # Position above health bar
        
        indicator_info = {
            "surface": text_surface,
            "position": [start_x, start_y], # List for mutable position
            "alpha": 255,
            "lifetime_ms": self.damage_indicator_lifetime_ms,
            "creation_time_ms": pygame.time.get_ticks(),
            "float_speed_y": self.damage_indicator_float_speed_y 
        }
        self.damage_indicators.append(indicator_info)
        # --- End Damage Indicator Creation ---
        
        # Original console print (can be kept or removed)
        # print(f"Player {self.team.name} took {actual_damage} damage. Health: {self.health}/{self.config.get('game', {}).get('player', {}).get('max_health', 100)}")

        if self.health <= 0:
            self.health = 0
            self.alive = False
            # print(f"Player {self.team.name} has been defeated.") # Original print
            if self.game_manager: # Check if game_manager is set
                self.game_manager.is_game_over() 

    def process_explosion_damage(self, 
                                 gradient_origin: Tuple[int, int], 
                                 damage_gradient: np.ndarray,
                                 directly_hit_player_from_impact: Optional['Player'], # <<< NEW ARG
                                 weapon_configured_center_damage: int # <<< NEW ARG
                                 ) -> None:
        if not self.alive or damage_gradient is None or damage_gradient.size == 0:
            return

        max_damage_taken = 0
        radius_sq = self.radius * self.radius

        grad_rows, grad_cols = damage_gradient.shape
        circle_center_in_grad_x = self.x - gradient_origin[0]
        circle_center_in_grad_y = self.y - gradient_origin[1]

        min_gx = max(0, int(circle_center_in_grad_x - self.radius))
        max_gx = min(grad_cols - 1, int(circle_center_in_grad_x + self.radius))
        min_gy = max(0, int(circle_center_in_grad_y - self.radius))
        max_gy = min(grad_rows - 1, int(circle_center_in_grad_y + self.radius))
        
        for r_idx in range(min_gy, max_gy + 1): 
            for c_idx in range(min_gx, max_gx + 1): 
                grad_cell_center_x = float(c_idx) + 0.5
                grad_cell_center_y = float(r_idx) + 0.5
                dist_sq = (grad_cell_center_x - circle_center_in_grad_x)**2 + \
                          (grad_cell_center_y - circle_center_in_grad_y)**2
                
                if dist_sq < radius_sq: 
                    damage_value = damage_gradient[r_idx, c_idx]
                    if damage_value > max_damage_taken:
                        max_damage_taken = damage_value
        
        # --- NEW: Ensure direct hit gets at least configured center damage ---
        if directly_hit_player_from_impact is self:
            if weapon_configured_center_damage > max_damage_taken:
                print(f"Player {self.team.name} (Direct Hit): Overriding gradient damage {max_damage_taken} with configured center damage {weapon_configured_center_damage}")
                max_damage_taken = weapon_configured_center_damage
            elif max_damage_taken > 0 : # Only print if some damage was already calculated
                 print(f"Player {self.team.name} (Direct Hit): Gradient damage {max_damage_taken} meets/exceeds configured center damage {weapon_configured_center_damage}.")


        if max_damage_taken > 0:
            self.apply_damage(int(max_damage_taken))