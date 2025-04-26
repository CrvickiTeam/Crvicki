import pygame
from enum import Enum
import os
import math
import numpy as np

# Assuming Terrain and TerrainMaterial are importable if needed for type hints
from .terrain import Terrain, TerrainMaterial # Make sure Terrain is imported

class PlayerTeam(Enum):
    TEAM_1 = 1
    TEAM_2 = 2

DEFAULT_PLAYER_SPEED = 100
DEFAULT_PLAYER_WIDTH = 20
DEFAULT_PLAYER_HEIGHT = 20
GRAVITY = 400
MAX_STEP_HEIGHT = 4
# --- Aiming Constants ---
AIM_ANGLE_RATE = 60 # Degrees per second
AIM_POWER_RATE = 50 # Power units per second
MIN_AIM_POWER = 10
MAX_AIM_POWER = 120
DEFAULT_AIM_POWER = 50

class Player:
    def __init__(self, start_pos: tuple[int, int], team: PlayerTeam, config: dict) -> None:
        self.config = config
        self.team = team
        self.alive = True

        self.x, self.y = float(start_pos[0]), float(start_pos[1])
        self.angle = 0.0
        self.direction = 1 # 1 for right, -1 for left

        self.speed = self.config.get("player", {}).get("speed", DEFAULT_PLAYER_SPEED)
        self.width = self.config.get("player", {}).get("width", DEFAULT_PLAYER_WIDTH)
        self.height = self.config.get("player", {}).get("height", DEFAULT_PLAYER_HEIGHT)

        self.vx = 0.0
        self.vy = 0.0
        self.is_grounded = False
        self.is_moving = False

        # --- Aiming Attributes ---
        # Angle relative to horizontal (0=right, 90=up, 180=left, -90=down)
        # Initial angle depends on direction
        self.aim_angle = 45.0 if self.direction == 1 else 135.0
        self.aim_power = DEFAULT_AIM_POWER

        self.rect = pygame.Rect(0, 0, self.width, self.height)
        self.rect.center = (int(self.x), int(self.y))

    def move_left(self):
        self.vx = -self.speed
        self.is_moving = True
        if self.direction == 1:
            self.direction = -1
            # Reset aim angle when turning
            self.aim_angle = 135.0 # Point up-left

    def move_right(self):
        self.vx = self.speed
        self.is_moving = True
        if self.direction == -1:
            self.direction = 1
            # Reset aim angle when turning
            self.aim_angle = 45.0 # Point up-right

    def stop_moving(self):
        self.vx = 0.0
        self.is_moving = False

    # --- Aiming Methods ---
    def aim_up(self, dt: float):
        # Adjust angle based on direction
        if self.direction == 1: # Facing right
            self.aim_angle += AIM_ANGLE_RATE * dt
            self.aim_angle = min(self.aim_angle, 180.0) # Limit up-left
        else: # Facing left
            self.aim_angle -= AIM_ANGLE_RATE * dt
            self.aim_angle = max(self.aim_angle, 0.0) # Limit up-right

    def aim_down(self, dt: float):
        # Adjust angle based on direction
        if self.direction == 1: # Facing right
            self.aim_angle -= AIM_ANGLE_RATE * dt
            self.aim_angle = max(self.aim_angle, -90.0) # Limit down-right
        else: # Facing left
            self.aim_angle += AIM_ANGLE_RATE * dt
            self.aim_angle = min(self.aim_angle, 270.0) # Limit down-left

    def increase_power(self, dt: float):
        self.aim_power += AIM_POWER_RATE * dt
        self.aim_power = min(self.aim_power, MAX_AIM_POWER)

    def decrease_power(self, dt: float):
        self.aim_power -= AIM_POWER_RATE * dt
        self.aim_power = max(self.aim_power, MIN_AIM_POWER)

    def get_shot_info(self) -> tuple[float, float]:
        """Returns the current aim angle (degrees) and power."""
        return self.aim_angle, self.aim_power

    # --- Collision Check ---
    def _check_terrain_collision(self, rect: pygame.Rect, terrain: Terrain) -> bool:
        # ... (collision code remains the same) ...
        start_x = max(0, rect.left)
        end_x = min(terrain.width, rect.right)
        start_y = max(0, rect.top)
        end_y = min(terrain.height, rect.bottom)
        if start_x >= end_x or start_y >= end_y: return False
        grid_slice = terrain.logic_grid[start_x:end_x, start_y:end_y]
        return np.any(grid_slice != TerrainMaterial.EMPTY.value)

    # --- Update ---
    def update(self, dt: float, terrain: Terrain):
        # ... (movement and collision logic remains the same) ...
        if not self.alive or terrain is None: return

        # Horizontal Movement
        if self.is_moving:
            dx = self.vx * dt
            target_x = self.x + dx
            test_rect_x = self.rect.copy()
            test_rect_x.center = (int(target_x), int(self.y))
            blocked_by_boundary_x = False
            if test_rect_x.left < 0: target_x = self.width / 2; self.vx = 0; blocked_by_boundary_x = True
            elif test_rect_x.right > terrain.width: target_x = terrain.width - self.width / 2; self.vx = 0; blocked_by_boundary_x = True
            test_rect_x.center = (int(target_x), int(self.y))
            if not blocked_by_boundary_x and self._check_terrain_collision(test_rect_x, terrain):
                stepped_up = False
                for step in range(1, MAX_STEP_HEIGHT + 1):
                    test_rect_step = self.rect.copy(); test_rect_step.center = (int(target_x), int(self.y - step))
                    if not self._check_terrain_collision(test_rect_step, terrain):
                        self.x = target_x; self.y -= step; stepped_up = True; break
                if not stepped_up: self.vx = 0; target_x = self.x
            self.x = target_x

        # Vertical Movement
        if not self.is_grounded: self.vy += GRAVITY * dt
        dy = self.vy * dt
        target_y = self.y + dy
        test_rect_y = self.rect.copy(); test_rect_y.center = (int(self.x), int(target_y))
        blocked_by_boundary_y = False
        if test_rect_y.top < 0: target_y = self.height / 2; self.vy = 0; blocked_by_boundary_y = True
        elif test_rect_y.bottom > terrain.height: target_y = terrain.height - self.height / 2; self.vy = 0; self.is_grounded = True; blocked_by_boundary_y = True
        test_rect_y.center = (int(self.x), int(target_y))
        if not blocked_by_boundary_y and self._check_terrain_collision(test_rect_y, terrain):
            while self._check_terrain_collision(test_rect_y, terrain): test_rect_y.bottom -= 1; target_y = test_rect_y.centery
            self.y = target_y; self.vy = 0; self.is_grounded = True
            # Angle Calculation
            center_x = int(self.x); ground_y = test_rect_y.bottom
            left_x = max(0, center_x - self.width // 4); right_x = min(terrain.width - 1, center_x + self.width // 4)
            left_y = ground_y; right_y = ground_y
            for y_scan in range(ground_y - 1, ground_y + 5):
                 if y_scan >= terrain.height: break
                 if terrain.logic_grid[left_x, y_scan] != 0: left_y = y_scan; break
            for y_scan in range(ground_y - 1, ground_y + 5):
                 if y_scan >= terrain.height: break
                 if terrain.logic_grid[right_x, y_scan] != 0: right_y = y_scan; break
            delta_x = (right_x - left_x); delta_y = (right_y - left_y)
            if delta_x != 0: self.angle = -math.degrees(math.atan2(delta_y, delta_x))
            else: self.angle = 0.0
        elif not blocked_by_boundary_y: self.y = target_y; self.is_grounded = False
        elif blocked_by_boundary_y: self.y = target_y

        self.rect.center = (int(self.x), int(self.y))
        self.stop_moving()

    # --- Draw ---
    def draw(self, screen: pygame.Surface):
        if not self.alive:
            return

        # Draw Rotated Hitbox
        half_w, half_h = self.width / 2, self.height / 2
        points = [(-half_w, -half_h), ( half_w, -half_h), ( half_w,  half_h), (-half_w,  half_h)]
        angle_rad = math.radians(self.angle); cos_a, sin_a = math.cos(angle_rad), math.sin(angle_rad)
        rotated_points = []
        for px, py in points:
            x_rot = px * cos_a - py * sin_a; y_rot = px * sin_a + py * cos_a
            rotated_points.append((int(self.x + x_rot), int(self.y + y_rot)))
        hitbox_color = (255, 0, 0) if self.team == PlayerTeam.TEAM_1 else (0, 0, 255)
        pygame.draw.polygon(screen, hitbox_color, rotated_points, 1)

        # Draw center dot
        center_color = (255, 255, 0); pygame.draw.circle(screen, center_color, (int(self.x), int(self.y)), 3)

        # --- Draw Aiming Indicator ---
        # Calculate end point based on aim_angle and aim_power
        aim_rad = math.radians(self.aim_angle)
        # Power scales the length, map MAX_AIM_POWER to a reasonable line length (e.g., 50 pixels)
        line_length = (self.aim_power / MAX_AIM_POWER) * 50
        end_x = self.x + line_length * math.cos(aim_rad)
        end_y = self.y - line_length * math.sin(aim_rad) # Subtract because pygame y is inverted

        pygame.draw.line(screen, (255, 255, 255), (int(self.x), int(self.y)), (int(end_x), int(end_y)), 2)
