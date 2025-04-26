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
MAX_STEP_HEIGHT = 4 # Max pixels the player can step up automatically

class Player:
    def __init__(self, start_pos: tuple[int, int], team: PlayerTeam, config: dict) -> None:
        self.config = config
        self.team = team
        self.alive = True

        # Use center-center as the logical position
        self.x, self.y = float(start_pos[0]), float(start_pos[1])
        self.angle = 0.0
        self.direction = 1 # 1 for right, -1 for left

        self.speed = self.config.get("player", {}).get("speed", DEFAULT_PLAYER_SPEED)
        self.width = self.config.get("player", {}).get("width", DEFAULT_PLAYER_WIDTH)
        self.height = self.config.get("player", {}).get("height", DEFAULT_PLAYER_HEIGHT)

        # Velocity and state
        self.vx = 0.0 # Horizontal velocity (set by move methods)
        self.vy = 0.0 # Vertical velocity
        self.is_grounded = False
        self.is_moving = False # Flag to indicate if move keys are pressed

        # Initialize rect based on center-center
        self.rect = pygame.Rect(0, 0, self.width, self.height)
        self.rect.center = (int(self.x), int(self.y))

    def move_left(self):
        self.vx = -self.speed
        self.is_moving = True
        if self.direction == 1:
            self.direction = -1

    def move_right(self):
        self.vx = self.speed
        self.is_moving = True
        if self.direction == -1:
            self.direction = 1

    def stop_moving(self):
        self.vx = 0.0
        self.is_moving = False

    def _check_terrain_collision(self, rect: pygame.Rect, terrain: Terrain) -> bool:
        """Checks if the given rect overlaps with any solid terrain pixels."""
        # Iterate through the grid cells covered by the rect
        start_x = max(0, rect.left)
        end_x = min(terrain.width, rect.right)
        start_y = max(0, rect.top)
        end_y = min(terrain.height, rect.bottom)

        if start_x >= end_x or start_y >= end_y: # Rect is fully outside bounds
            return False

        # Check the corresponding slice in the logic grid
        # Assuming terrain.logic_grid uses [x, y] indexing
        grid_slice = terrain.logic_grid[start_x:end_x, start_y:end_y]

        # Check if any pixel in the slice is not EMPTY (value 0)
        return np.any(grid_slice != TerrainMaterial.EMPTY.value)


    def update(self, dt: float, terrain: Terrain):
        if not self.alive or terrain is None:
            return

        # --- Horizontal Movement and Collision ---
        if self.is_moving:
            dx = self.vx * dt
            target_x = self.x + dx
            test_rect_x = self.rect.copy()
            test_rect_x.center = (int(target_x), int(self.y))

            # --- Boundary Check (Horizontal) ---
            blocked_by_boundary_x = False
            if test_rect_x.left < 0:
                target_x = self.width / 2 # Snap center so left edge is at 0
                self.vx = 0
                blocked_by_boundary_x = True
            elif test_rect_x.right > terrain.width:
                target_x = terrain.width - self.width / 2 # Snap center so right edge is at width
                self.vx = 0
                blocked_by_boundary_x = True

            # Update test_rect_x position after potential boundary snap
            test_rect_x.center = (int(target_x), int(self.y))

            # --- Terrain Collision Check (Horizontal) ---
            # Only check terrain if not already blocked by boundary
            if not blocked_by_boundary_x and self._check_terrain_collision(test_rect_x, terrain):
                # Collision detected horizontally, try stepping up
                stepped_up = False
                for step in range(1, MAX_STEP_HEIGHT + 1):
                    test_rect_step = self.rect.copy()
                    test_rect_step.center = (int(target_x), int(self.y - step))
                    if not self._check_terrain_collision(test_rect_step, terrain):
                        # Found a step height that works
                        self.x = target_x
                        self.y -= step # Move player up
                        stepped_up = True
                        break # Stop checking steps
                if not stepped_up:
                    # Couldn't step up, block horizontal movement
                    self.vx = 0 # Stop horizontal velocity if blocked
                    # Don't update self.x if fully blocked
                    target_x = self.x # Revert target_x if blocked by terrain
            # else: # No horizontal terrain collision (or already handled boundary)
            #     self.x = target_x # Allow movement if no collision

            # Update final horizontal position
            self.x = target_x

        # --- Vertical Movement and Collision ---
        if not self.is_grounded:
            self.vy += GRAVITY * dt

        dy = self.vy * dt
        target_y = self.y + dy
        test_rect_y = self.rect.copy()
        # Use the potentially updated x position for the vertical check
        test_rect_y.center = (int(self.x), int(target_y))

        # --- Boundary Check (Vertical) ---
        blocked_by_boundary_y = False
        if test_rect_y.top < 0:
            target_y = self.height / 2 # Snap center so top edge is at 0
            self.vy = 0 # Stop upward velocity
            blocked_by_boundary_y = True
        elif test_rect_y.bottom > terrain.height:
            target_y = terrain.height - self.height / 2 # Snap center so bottom edge is at height
            self.vy = 0
            self.is_grounded = True # Treat bottom boundary as ground
            blocked_by_boundary_y = True

        # Update test_rect_y position after potential boundary snap
        test_rect_y.center = (int(self.x), int(target_y))

        # --- Terrain Collision Check (Vertical) ---
        # Only check terrain if not already blocked by boundary
        if not blocked_by_boundary_y and self._check_terrain_collision(test_rect_y, terrain):
            # Vertical collision detected (likely hitting ground)
            # Snap position: Move rect up until it doesn't collide
            while self._check_terrain_collision(test_rect_y, terrain):
                test_rect_y.bottom -= 1
                target_y = test_rect_y.centery # Adjust target_y based on snapping

            self.y = target_y
            self.vy = 0
            self.is_grounded = True

            # --- Calculate Angle ---
            center_x = int(self.x)
            ground_y = test_rect_y.bottom # Y level of the ground the rect is resting on

            left_x = max(0, center_x - self.width // 4)
            right_x = min(terrain.width - 1, center_x + self.width // 4)

            # Find ground height slightly to the left (scan down from slightly above ground_y)
            left_y = ground_y
            for y_scan in range(ground_y - 1, ground_y + 5):
                 if y_scan >= terrain.height: break
                 if terrain.logic_grid[left_x, y_scan] != 0:
                     left_y = y_scan
                     break

            # Find ground height slightly to the right
            right_y = ground_y
            for y_scan in range(ground_y - 1, ground_y + 5):
                 if y_scan >= terrain.height: break
                 if terrain.logic_grid[right_x, y_scan] != 0:
                     right_y = y_scan
                     break

            delta_x = (right_x - left_x)
            delta_y = (right_y - left_y) # Note: Higher y means lower on screen
            if delta_x != 0:
                self.angle = -math.degrees(math.atan2(delta_y, delta_x))
            else:
                self.angle = 0.0

        elif not blocked_by_boundary_y: # No vertical terrain collision and not blocked by boundary
            self.y = target_y
            self.is_grounded = False
            # Optionally reset angle when airborne
            # self.angle = 0.0
        elif blocked_by_boundary_y: # Was blocked by boundary, ensure y is set
             self.y = target_y # Use the boundary-snapped target_y


        # --- Final Update Rect Position ---
        self.rect.center = (int(self.x), int(self.y))

        # Reset horizontal movement intention for next frame
        self.stop_moving()


    def draw(self, screen: pygame.Surface):
        if not self.alive:
            return

        # --- Draw Rotated Hitbox (for visualization) ---
        # Create points for the original rect corners relative to center
        half_w, half_h = self.width / 2, self.height / 2
        points = [
            (-half_w, -half_h), ( half_w, -half_h),
            ( half_w,  half_h), (-half_w,  half_h)
        ]
        # Rotate points around origin (0,0)
        angle_rad = math.radians(self.angle)
        cos_a, sin_a = math.cos(angle_rad), math.sin(angle_rad)
        rotated_points = []
        for x, y in points:
            x_rot = x * cos_a - y * sin_a
            y_rot = x * sin_a + y * cos_a
            # Translate points to player's actual position
            rotated_points.append((int(self.x + x_rot), int(self.y + y_rot)))

        hitbox_color = (255, 0, 0) if self.team == PlayerTeam.TEAM_1 else (0, 0, 255)
        pygame.draw.polygon(screen, hitbox_color, rotated_points, 1) # Draw rotated polygon outline

        # Draw center dot
        center_color = (255, 255, 0) # Yellow
        pygame.draw.circle(screen, center_color, (int(self.x), int(self.y)), 3)