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
    # REMOVE Class attributes:
    # AIM_MAX_UP_DEGREES = 90.0
    # AIM_MIN_DOWN_DEGREES_OFFSET = -10.0

    def __init__(self, start_pos: tuple[int, int], team: PlayerTeam, config: Dict[str, Any], game_manager: 'GameManager') -> None:
        self.config: Dict[str, Any] = config
        self.team: PlayerTeam = team
        self.game_manager: 'GameManager' = game_manager 
        self.alive: bool = True
        
        self.x: float = float(start_pos[0])
        self.y: float = float(start_pos[1])
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

        self.width: int = int(hitbox_cfg.get("width", 20)) 
        self.height: int = int(hitbox_cfg.get("height", 20)) 

        self.aim_angle_rate: float = float(aiming_cfg.get("angle_change_rate", 60.0))
        self.aim_power_rate: float = float(aiming_cfg.get("power_change_rate", 50.0))
        self.min_aim_power: float = float(aiming_cfg.get("min_power", 10.0))
        self.max_aim_power: float = float(aiming_cfg.get("max_power", 135.0))
        self.default_aim_power: float = float(aiming_cfg.get("default_power", 50.0))
        self.aim_power: float = self.default_aim_power

        # Load aiming angle limits from config
        self.aim_max_up_degrees: float = float(aiming_cfg.get("max_up_degrees", 90.0)) # <<< NEW
        self.aim_min_down_degrees_offset: float = float(aiming_cfg.get("min_down_degrees_offset", -10.0)) # <<< NEW


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
        self.load_sprites() # This will load and potentially set initial width/height from sprites

        # If config specifies dimensions, use them to scale sprites
        # This logic seems to be what you had: load sprites, then if config has w/h, scale them.
        loaded_cfg_width: Optional[int] = hitbox_cfg.get("width")
        loaded_cfg_height: Optional[int] = hitbox_cfg.get("height")

        if self.active_tank_image_orig: # Check if sprite loaded
            # If config provides dimensions, scale the loaded sprite and update self.width/height
            if loaded_cfg_width is not None and loaded_cfg_height is not None:
                self.width = loaded_cfg_width
                self.height = loaded_cfg_height
                self.active_tank_image_orig = pygame.transform.scale(self.active_tank_image_orig, (self.width, self.height))
                if self.waiting_tank_image_orig:
                    self.waiting_tank_image_orig = pygame.transform.scale(self.waiting_tank_image_orig, (self.width, self.height))
            else: # Otherwise, use the sprite's own dimensions
                self.width = self.active_tank_image_orig.get_width()
                self.height = self.active_tank_image_orig.get_height()
        elif loaded_cfg_width is not None and loaded_cfg_height is not None:
            # No sprite, but config has dimensions (e.g., for placeholder)
            self.width = loaded_cfg_width
            self.height = loaded_cfg_height
        # else self.width/height remain the initial defaults from hitbox_cfg if no sprite and no specific w/h in cfg

        self.rect: pygame.Rect = pygame.Rect(0, 0, self.width, self.height)
        self.rect.center = (int(self.x), int(self.y))


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
        except pygame.error as e:
            print(f"Error loading player sprites: {e}")
            try:
                placeholder_path = os.path.join(project_root, "assets", "graphics",
                                                "missing.png")  # Pot do missing.png v assets/graphics
                placeholder_img = pygame.image.load(placeholder_path).convert_alpha()
                ph_width = self.width
                ph_height = self.height

                if self.active_tank_image_orig is None:
                    self.active_tank_image_orig = pygame.transform.scale(placeholder_img, (ph_width, ph_height))
                if self.waiting_tank_image_orig is None:
                    self.waiting_tank_image_orig = pygame.transform.scale(placeholder_img, (ph_width, ph_height))
                if self.pipe_image_orig is None:
                    self.pipe_image_orig = pygame.transform.scale(placeholder_img, (
                    max(1, ph_width // 2), max(1, ph_height // 4)))  # Zagotovi pozitivne dimenzije
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
                                                          pygame.SRCALPHA)  # Zagotovi pozitivne dimenzije
                    self.pipe_image_orig.fill((255, 0, 255, 128))

    # --- Movement ---
    def move_left(self) -> None:
        old_direction = self.direction
        self.direction = -1

        if old_direction != self.direction: # If direction actually changed
            # Mirror the aim_angle to maintain its visual orientation relative to the world
            self.aim_angle = 180.0 - self.aim_angle
            # The existing aim_up/aim_down methods will clamp this to valid ranges for the new direction

        if self.distance_moved_this_turn < self.max_move_distance_per_turn:
            self.is_moving = True
            self.vx = -self.speed
        else:
            # No fuel to initiate movement, ensure player is not set to move
            self.vx = 0
            self.is_moving = False 

    def move_right(self) -> None:
        old_direction = self.direction
        self.direction = 1

        if old_direction != self.direction: # If direction actually changed
            # Mirror the aim_angle to maintain its visual orientation relative to the world
            self.aim_angle = 180.0 - self.aim_angle
            # The existing aim_up/aim_down methods will clamp this to valid ranges for the new direction

        if self.distance_moved_this_turn < self.max_move_distance_per_turn:
            self.is_moving = True
            self.vx = self.speed
        else:
            # No fuel to initiate movement, ensure player is not set to move
            self.vx = 0
            self.is_moving = False

    def stop_moving(self) -> None:
        self.is_moving = False
        self.vx = 0.0

    # --- Aiming ---
    # (Your existing aim_up, aim_down, increase_power, decrease_power methods remain unchanged)
    # Make sure they use self.aim_max_up_degrees and self.aim_min_down_degrees_offset from config
    def aim_up(self, dt: float) -> None:
        if self.direction == 1: # Facing right
            self.aim_angle += self.aim_angle_rate * dt 
            self.aim_angle = min(self.aim_angle, self.aim_max_up_degrees) 
        else: # Facing left
            self.aim_angle -= self.aim_angle_rate * dt 
            self.aim_angle = max(self.aim_angle, self.aim_max_up_degrees) 

    def aim_down(self, dt: float) -> None:
        if self.direction == 1: # Facing right
            self.aim_angle -= self.aim_angle_rate * dt 
            self.aim_angle = max(self.aim_angle, self.aim_min_down_degrees_offset) 
        else: # Facing left
            self.aim_angle += self.aim_angle_rate * dt 
            max_down_angle_left_facing = 180.0 - self.aim_min_down_degrees_offset 
            self.aim_angle = min(self.aim_angle, max_down_angle_left_facing)

    def increase_power(self, dt: float) -> None:
        self.aim_power += self.aim_power_rate * dt # Use instance attribute
        self.aim_power = min(self.aim_power, self.max_aim_power) # Use instance attribute

    def decrease_power(self, dt: float) -> None:
        self.aim_power -= self.aim_power_rate * dt # Use instance attribute
        self.aim_power = max(self.aim_power, self.min_aim_power) # Use instance attribute

    def get_shot_info(self) -> tuple[float, float]:
        """Returns the current aim angle (degrees) and power."""
        return self.aim_angle, self.aim_power

    # --- Collision Check ---
    def _check_terrain_collision(self, rect: pygame.Rect, terrain: Terrain) -> bool:
        start_x = max(0, rect.left)
        end_x = min(terrain.width, rect.right)
        start_y = max(0, rect.top)
        end_y = min(terrain.height, rect.bottom)
        if start_x >= end_x or start_y >= end_y: return False
        # Use Enum value for check
        grid_slice = terrain.logic_grid[start_x:end_x, start_y:end_y]
        return np.any(grid_slice != TerrainMaterial.EMPTY.value)

    # --- Update ---
    def update(self, dt: float, terrain: Terrain) -> None:
        if not self.alive or terrain is None: return

        x_at_start_of_frame_horizontal_phase: float = self.x # <<< INITIALIZE HERE

        # Horizontal Movement
        if self.is_moving: # True if move_left/right was called and had fuel
            potential_dx: float = self.vx * dt 
            remaining_fuel: float = self.max_move_distance_per_turn - self.distance_moved_this_turn
            
            dx_to_apply_this_frame: float

            if remaining_fuel <= 0:
                dx_to_apply_this_frame = 0.0
                self.stop_moving() # Ensure is_moving is false and vx is 0
            elif abs(potential_dx) > remaining_fuel:
                dx_to_apply_this_frame = math.copysign(remaining_fuel, potential_dx)
            else:
                dx_to_apply_this_frame = potential_dx
            
            if dx_to_apply_this_frame == 0.0 and self.vx != 0.0: # If intended to move but fuel cap resulted in no movement
                self.stop_moving()

            target_x: float = self.x + dx_to_apply_this_frame
            
            # --- Collision and application of horizontal movement ---
            final_x_after_horizontal_pass: float = target_x # Start with fuel-adjusted target

            test_rect_x: pygame.Rect = self.rect.copy()
            test_rect_x.center = (int(final_x_after_horizontal_pass), int(self.y))
            
            blocked_by_boundary_x: bool = False
            if test_rect_x.left < 0:
                final_x_after_horizontal_pass = self.width / 2.0 
                blocked_by_boundary_x = True
            elif test_rect_x.right > terrain.width:
                final_x_after_horizontal_pass = terrain.width - self.width / 2.0
                blocked_by_boundary_x = True
            
            test_rect_x.center = (int(final_x_after_horizontal_pass), int(self.y))

            original_y_before_step_attempt: float = self.y
            if not blocked_by_boundary_x and self._check_terrain_collision(test_rect_x, terrain):
                stepped_up: bool = False
                for step in range(1, self.max_step_height + 1):
                    test_rect_step: pygame.Rect = self.rect.copy()
                    test_rect_step.center = (int(final_x_after_horizontal_pass), int(self.y - step))
                    if not self._check_terrain_collision(test_rect_step, terrain):
                        self.y -= step # Apply y change from stepping
                        stepped_up = True
                        self.is_grounded = True # Crucial: if we stepped up, we are on ground
                        self.vy = 0             # Crucial: reset vertical velocity
                        break 
                if not stepped_up:
                    final_x_after_horizontal_pass = x_at_start_of_frame_horizontal_phase # Cannot move, revert x
                    self.y = original_y_before_step_attempt # Revert y if step attempt failed
            
            self.x = final_x_after_horizontal_pass
            
            # Update fuel consumed based on actual horizontal displacement this frame
            # This line was the problem if self.is_moving was false initially:
            actual_horizontal_displacement_this_frame: float = abs(self.x - x_at_start_of_frame_horizontal_phase)
            self.distance_moved_this_turn += actual_horizontal_displacement_this_frame

            if self.distance_moved_this_turn >= self.max_move_distance_per_turn:
                self.distance_moved_this_turn = self.max_move_distance_per_turn # Cap it
                if self.is_moving: # If was actively trying to move when fuel ran out
                    self.stop_moving()
        # else: # If not self.is_moving (e.g. input stopped, or fuel ran out on previous frame)
            # self.vx = 0.0 # Ensure vx is 0 if not actively moving. stop_moving() handles this.
            # The GameScene is responsible for calling move_left/right. If it doesn't, is_moving will become false
            # after one frame if stop_moving() is called at the end of update or if fuel runs out.
            # If GameScene stops calling move_left/right, self.is_moving might be true from last frame.
            # The stop_moving() in move_left/right if fuel is out, and the one after distance_moved_this_turn update,
            # are key. If GameScene doesn't call move_left/right, self.is_moving will be false from reset_turn_state
            # or from previous frame's stop_moving().
            pass


        # Vertical Movement (Gravity)
        # Assume self.is_grounded is from the PREVIOUS frame or from a step-up in THIS frame.
        if not self.is_grounded:
            self.vy += self.gravity * dt
        else: # If grounded from previous frame/step-up, ensure vy is 0 before calculating dy
            self.vy = 0 
        
        dy: float = self.vy * dt 
        target_y_gravity: float = self.y + dy
        
        current_x_int = int(self.x) # Use the already resolved x for vertical checks

        prospective_rect_y: pygame.Rect = self.rect.copy()
        prospective_rect_y.centerx = current_x_int 
        prospective_rect_y.centery = int(target_y_gravity)

        new_is_grounded_this_frame = False # Re-evaluate grounded state based on this frame's vertical pass

        # Boundary checks for y
        if prospective_rect_y.top < 0: # Hit ceiling
            prospective_rect_y.top = 0
            self.y = float(prospective_rect_y.centery)
            self.vy = 0 
            new_is_grounded_this_frame = False # Hitting ceiling doesn't mean grounded
        elif prospective_rect_y.bottom > terrain.height: # Hit bottom of world
            prospective_rect_y.bottom = terrain.height
            self.y = float(prospective_rect_y.centery)
            self.vy = 0
            new_is_grounded_this_frame = True
        else:
            # Terrain collision check for y
            if self._check_terrain_collision(prospective_rect_y, terrain):
                if dy >= 0: # Moving downwards or stationary and embedded -> Landed on something
                    while self._check_terrain_collision(prospective_rect_y, terrain):
                        prospective_rect_y.bottom -= 1
                        if prospective_rect_y.top < -self.height * 2 : break # Safety break
                    # After loop, prospective_rect_y.bottom is the y-coord of the first pixel *above* the ground.
                    # So, the player's actual rect bottom should be this value.
                    self.rect.bottom = prospective_rect_y.bottom + 1 # Place bottom on the surface
                    self.y = float(self.rect.centery)
                    self.vy = 0
                    new_is_grounded_this_frame = True
                elif dy < 0: # Moving upwards and hit something (like a platform from below)
                    while self._check_terrain_collision(prospective_rect_y, terrain):
                        prospective_rect_y.top += 1
                        if prospective_rect_y.bottom > terrain.height + self.height*2 : break # Safety
                    self.rect.top = prospective_rect_y.top -1 # Place top just below the surface hit
                    self.y = float(self.rect.centery)
                    self.vy = 0 
                    new_is_grounded_this_frame = False # Hitting something from below is not grounded
            else: # No collision with terrain at prospective_rect_y: potentially airborne
                self.y = target_y_gravity # Apply the gravity move
                
                # "Sticky Feet" / Downward Probe: Check if ground is immediately below
                # This helps prevent bobbing if player is 1px above ground due to float inaccuracies
                # or small horizontal shifts.
                if dy >= 0: # Only probe if moving down or was stationary (vy might have been 0)
                    probe_rect = prospective_rect_y.copy() # Start from where player would be after gravity
                    probe_rect.top += 1 # Move down 1 pixel to check for ground just beneath
                    
                    if self._check_terrain_collision(probe_rect, terrain):
                        # Ground is 1 pixel below! Snap to it.
                        while self._check_terrain_collision(probe_rect, terrain):
                            probe_rect.bottom -= 1
                            if probe_rect.top < -self.height * 2: break # Safety
                        self.rect.bottom = probe_rect.bottom + 1
                        self.y = float(self.rect.centery)
                        self.vy = 0
                        new_is_grounded_this_frame = True
                    else:
                        # Truly airborne
                        new_is_grounded_this_frame = False
                else: # Was moving upwards and didn't hit anything
                    new_is_grounded_this_frame = False


        self.is_grounded = new_is_grounded_this_frame

        # Angle Calculation (based on final grounded position)
        if self.is_grounded:
            center_x_angle: int = int(self.x)
            ground_y_contact_angle: int = int(self.y + self.height / 2.0) # Bottom of the player

            left_x_angle: int = max(0, center_x_angle - self.width // 4)
            right_x_angle: int = min(terrain.width - 1, center_x_angle + self.width // 4)
            
            left_y_angle: int = ground_y_contact_angle
            right_y_angle: int = ground_y_contact_angle

            scan_range_y_angle: int = self.max_step_height + 2 # How far to scan for ground

            for y_scan_offset in range(-scan_range_y_angle, scan_range_y_angle):
                y_check_left = min(terrain.height -1, max(0, ground_y_contact_angle + y_scan_offset))
                if terrain.logic_grid[left_x_angle, y_check_left] != TerrainMaterial.EMPTY.value:
                    left_y_angle = y_check_left
                    break
            for y_scan_offset in range(-scan_range_y_angle, scan_range_y_angle):
                y_check_right = min(terrain.height -1, max(0, ground_y_contact_angle + y_scan_offset))
                if terrain.logic_grid[right_x_angle, y_check_right] != TerrainMaterial.EMPTY.value:
                    right_y_angle = y_check_right
                    break
            
            delta_x_val_angle: int = (right_x_angle - left_x_angle)
            delta_y_val_angle: int = (right_y_angle - left_y_angle)
            if delta_x_val_angle != 0:
                self.angle = -math.degrees(math.atan2(delta_y_val_angle, delta_x_val_angle))
            else:
                self.angle = 0.0
        # else: # If not grounded, maintain current angle or set to 0
            # self.angle = 0.0 # Optional: reset angle if airborne

        self.rect.center = (int(self.x), int(self.y))

        # If GameScene is not calling move_left/right (keys released), is_moving will be false
        # from the previous frame's stop_moving or from reset_turn_state.
        # vx would be 0. So, no explicit stop_moving() needed at the very end of update here
        # if the input handling in GameScene and fuel logic in Player are correct.

    # --- Draw ---
    def draw(self, screen: pygame.Surface) -> None:
        if not self.alive:
            return

        is_active_player = (self.game_manager.get_active_player() == self)

        # === 1. PRIPRAVA SLIKE TANKA ===
        base_tank_sprite = self.active_tank_image_orig if is_active_player else self.waiting_tank_image_orig

        pipe_anchor_on_screen_x = self.x  # Privzeto, če spodnji izračun ne uspe
        pipe_anchor_on_screen_y = self.y

        if base_tank_sprite:
            tank_surface_to_render = pygame.transform.flip(base_tank_sprite, True,
                                                           False) if self.direction == -1 else base_tank_sprite
            rotated_tank_surface = pygame.transform.rotate(tank_surface_to_render, self.angle)
            tank_render_rect = rotated_tank_surface.get_rect(center=(int(self.x), int(self.y)))
            screen.blit(rotated_tank_surface, tank_render_rect.topleft)
        else:
            # Rezervni način prikaza (hitbox kot pravokotnik)
            half_w, half_h = self.width / 2, self.height / 2
            points = [(-half_w, -half_h), (half_w, -half_h), (half_w, half_h), (-half_w, half_h)]
            angle_rad = math.radians(self.angle)
            cos_a, sin_a = math.cos(angle_rad), math.sin(angle_rad)
            rotated_points = [
                (int(self.x + px * cos_a - py * sin_a), int(self.y + px * sin_a + py * cos_a))
                for px, py in points
            ]
            hitbox_color = (255, 0, 0) if self.team == PlayerTeam.TEAM_1 else (0, 0, 255)
            pygame.draw.polygon(screen, hitbox_color, rotated_points, 1)
            pygame.draw.circle(screen, (255, 255, 0), (int(self.x), int(self.y)), 3)

        # === 2. CEV IN INDIKATOR (samo za aktivnega igralca) ===
        if not is_active_player:
            return

        # A. Izračun sidrišča cevi
        anchor_x, anchor_y = self.x, self.y
        if self.active_tank_image_orig:
            local_anchor_x, local_anchor_y = 20, 22
            offset_x = local_anchor_x - self.active_tank_image_orig.get_width() / 2
            offset_y = local_anchor_y - self.active_tank_image_orig.get_height() / 2

            if self.direction == -1:
                offset_x *= -1

            body_angle_rad = math.radians(self.angle)
            rotated_offset_x = offset_x * math.cos(body_angle_rad) - offset_y * math.sin(body_angle_rad)
            rotated_offset_y = offset_x * math.sin(body_angle_rad) + offset_y * math.cos(body_angle_rad)
            anchor_x += rotated_offset_x
            anchor_y += rotated_offset_y

        # B. Izris cevi
        if self.pipe_image_orig:
            pipe_pivot_x, pipe_pivot_y = 20, 22
            image_to_rotate = self.pipe_image_orig
            pivot_x_on_image = pipe_pivot_x

            if self.direction == -1:
                image_to_rotate = pygame.transform.flip(image_to_rotate, True, False)
                pivot_x_on_image = image_to_rotate.get_width() - pipe_pivot_x
            
            # Rotacija slike
            pygame_rotation_angle = self.aim_angle
            vector_rotation_angle = self.aim_angle

            image_rect = image_to_rotate.get_rect()
            pivot_vec = pygame.math.Vector2(pivot_x_on_image - image_rect.centerx,
                                            pipe_pivot_y - image_rect.centery)
            rotated_image = pygame.transform.rotate(image_to_rotate, pygame_rotation_angle)
            rotated_rect = rotated_image.get_rect()
            rotated_pivot_vec = pivot_vec.rotate(-vector_rotation_angle)

            rotated_rect.center = (anchor_x - rotated_pivot_vec.x, anchor_y - rotated_pivot_vec.y)
            screen.blit(rotated_image, rotated_rect.topleft)



        # C. Izris belega indikatorja moči strela
        start_x, start_y = anchor_x, anchor_y
        if self.pipe_image_orig:
            dist_pivot_to_tip = self.pipe_image_orig.get_width() - 20
            aim_rad = math.radians(self.aim_angle)
            tip_offset_x = dist_pivot_to_tip * math.cos(aim_rad)
            tip_offset_y = -dist_pivot_to_tip * math.sin(aim_rad)
            start_x += tip_offset_x
            start_y += tip_offset_y

        aim_rad = math.radians(self.aim_angle)
        line_length = (self.aim_power / self.max_aim_power) * 50
        end_x = start_x + line_length * math.cos(aim_rad)
        end_y = start_y - line_length * math.sin(aim_rad)

        pygame.draw.line(screen, (255, 255, 255), (int(start_x), int(start_y)), (int(end_x), int(end_y)), 2)

        # Draw health bar
        bar_width = 40
        bar_height = 6
        fill = (self.health / 100) * bar_width

        # Health bar is narisan nad igralcem
        bar_x = self.x - bar_width // 2
        bar_y = self.y - self.height // 2 - 10
        pygame.draw.rect(screen, (255, 0, 0), (bar_x, bar_y, fill, bar_height))  # rdeče polnilo
        pygame.draw.rect(screen, (255, 255, 255), (bar_x, bar_y, bar_width, bar_height), 1)  # bel okvir
        
    def apply_damage(self, damage: int) -> None:
        if not self.alive:
            return
        self.health -= damage
        if self.health <= 0:
            self.health = 0
            self.alive = False
            self.game_manager.is_game_over()  # Check if game over condition is met

    def process_explosion_damage(self, gradient_origin: Tuple[int, int], damage_gradient: np.ndarray) -> None:
        """
        Calculates and applies damage to the player based on an explosion's damage gradient.
        Damage taken is the maximum value from the gradient that overlaps with the player's hitbox.
        """
        if not self.alive or damage_gradient is None or damage_gradient.size == 0:
            return

        player_rect = self.rect # Player's hitbox in world coordinates

        # Gradient's coverage in world coordinates
        grad_world_left = gradient_origin[0]
        grad_world_top = gradient_origin[1]
        grad_world_right = gradient_origin[0] + damage_gradient.shape[1]
        grad_world_bottom = gradient_origin[1] + damage_gradient.shape[0]

        # Calculate the overlapping rectangle in world coordinates
        overlap_left = max(player_rect.left, grad_world_left)
        overlap_top = max(player_rect.top, grad_world_top)
        overlap_right = min(player_rect.right, grad_world_right)
        overlap_bottom = min(player_rect.bottom, grad_world_bottom)

        # Check if there is any actual overlap
        if overlap_left < overlap_right and overlap_top < overlap_bottom:
            # Convert overlap world coordinates to indices within the damage_gradient array
            # Ensure indices are integers and within the bounds of the gradient array
            grad_idx_start_col = max(0, overlap_left - grad_world_left)
            grad_idx_end_col = max(0, overlap_right - grad_world_left)
            grad_idx_start_row = max(0, overlap_top - grad_world_top)
            grad_idx_end_row = max(0, overlap_bottom - grad_world_top)
            
            # Ensure end indices are not smaller than start indices for slicing
            grad_idx_end_col = max(grad_idx_start_col, grad_idx_end_col)
            grad_idx_end_row = max(grad_idx_start_row, grad_idx_end_row)


            # Slice the relevant part of the damage gradient
            # Ensure slices are within the actual dimensions of damage_gradient
            relevant_gradient_part = damage_gradient[
                grad_idx_start_row : min(grad_idx_end_row, damage_gradient.shape[0]),
                grad_idx_start_col : min(grad_idx_end_col, damage_gradient.shape[1])
            ]

            if relevant_gradient_part.size > 0:
                max_damage_value = np.max(relevant_gradient_part)
                if max_damage_value > 0:
                    # print(f"Player {self.team.name} hitbox overlaps with gradient. Max damage in overlap: {max_damage_value}")
                    self.apply_damage(int(max_damage_value))
            # else:
                # print(f"Player {self.team.name} hitbox overlaps, but relevant gradient part is empty.")
        # else:
            # print(f"Player {self.team.name} hitbox does not overlap with damage gradient.")