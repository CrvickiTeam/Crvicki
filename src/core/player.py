import pygame
from enum import Enum
import os
import math # Import math for angle calculation

# Assuming Terrain and TerrainMaterial are importable if needed for type hints
# from .terrain import Terrain, TerrainMaterial

class PlayerTeam(Enum):
    TEAM_1 = 1
    TEAM_2 = 2

DEFAULT_PLAYER_SPEED = 100
DEFAULT_PLAYER_WIDTH = 25
DEFAULT_PLAYER_HEIGHT = 25
GRAVITY = 100 # Pixels per second per second

class Player:
    def __init__(self, start_pos: tuple[int, int], team: PlayerTeam, config: dict) -> None:
        self.config = config
        self.team = team
        self.alive = True

        self.x, self.y = float(start_pos[0]), float(start_pos[1])
        self.angle = 0.0
        self.direction = 1

        self.speed = self.config.get("player", {}).get("speed", DEFAULT_PLAYER_SPEED)
        self.width = self.config.get("player", {}).get("width", DEFAULT_PLAYER_WIDTH)
        self.height = self.config.get("player", {}).get("height", DEFAULT_PLAYER_HEIGHT)

        self.vx = 0.0
        self.vy = 0.0
        self.is_grounded = False

        self.rect = pygame.Rect(0, 0, self.width, self.height)
        self.rect.midbottom = (int(self.x), int(self.y))

    def move_left(self, dt: float):
        self.x -= self.speed * dt
        if self.direction == 1:
            self.direction = -1

    def move_right(self, dt: float):
        self.x += self.speed * dt
        if self.direction == -1:
            self.direction = 1

    def update(self, dt: float, terrain): # Add type hint: terrain: Terrain
        if not self.alive or terrain is None:
            return

        # --- Apply Gravity ---
        if not self.is_grounded:
            self.vy += GRAVITY * dt

        # --- Update Position based on Velocity ---
        # Store previous position for collision response
        prev_x, prev_y = self.x, self.y
        self.x += self.vx * dt
        self.y += self.vy * dt

        # --- Simple Terrain Collision Check (Bottom-Center Point) ---
        check_x = int(self.x)
        check_y = int(self.y) # Check the pixel the bottom-center is currently at

        # Assume not grounded initially for this frame
        self.is_grounded = False

        # Check boundaries
        if 0 <= check_x < terrain.width and 0 <= check_y < terrain.height:
            # Check if the pixel at (check_x, check_y) is solid
            # Assuming terrain.logic_grid uses [x, y] indexing
            if terrain.logic_grid[check_x, check_y] != 0: # 0 is TerrainMaterial.EMPTY.value
                # Collision detected!
                self.is_grounded = True
                self.vy = 0
                # Snap the player's bottom-center (y) to the top of the collided pixel
                self.y = float(check_y)

                # --- Basic Angle Calculation (using points to the left and right) ---
                # Check points slightly to the left and right at the new ground level
                left_check_x = max(0, check_x - self.width // 4)
                right_check_x = min(terrain.width - 1, check_x + self.width // 4)
                ground_y = check_y # The y-level we landed on

                # Find ground height slightly to the left
                left_ground_y = ground_y
                for y_scan in range(ground_y, max(-1, ground_y - 5), -1):
                    if terrain.logic_grid[left_check_x, y_scan] == 0:
                        left_ground_y = y_scan + 1
                        break

                # Find ground height slightly to the right
                right_ground_y = ground_y
                for y_scan in range(ground_y, max(-1, ground_y - 5), -1):
                     if terrain.logic_grid[right_check_x, y_scan] == 0:
                         right_ground_y = y_scan + 1
                         break

                # Calculate angle using arctan2
                delta_x = (right_check_x - left_check_x)
                delta_y = (right_ground_y - left_ground_y)
                if delta_x != 0: # Avoid division by zero on flat ground
                    self.angle = -math.degrees(math.atan2(delta_y, delta_x))
                else:
                    self.angle = 0.0 # Flat ground

            # else: # Pixel below is empty, not grounded (already handled by default)
            #     self.is_grounded = False # Redundant, but explicit
        # else: # Player is outside terrain bounds horizontally or vertically
        #     self.is_grounded = False # Not grounded if off-screen

        # --- Update Rect Position (based on bottom-center) ---
        self.rect.midbottom = (int(self.x), int(self.y))


    def draw(self, screen: pygame.Surface):
        if not self.alive:
            return

        # Draw hitbox rectangle (rotated later if needed)
        hitbox_color = (255, 0, 0) if self.team == PlayerTeam.TEAM_1 else (0, 0, 255)
        # For now, draw the unrotated rect for simplicity
        pygame.draw.rect(screen, hitbox_color, self.rect, 1)

        # Draw bottom-center dot
        center_color = (255, 255, 0) # Yellow
        pygame.draw.circle(screen, center_color, (int(self.x), int(self.y)), 3) # Small circle

        # Optional: Draw angle indicator line
        line_len = 20
        end_x = self.x + line_len * math.cos(math.radians(-self.angle)) # Angle needs negation for pygame draw? Check this.
        end_y = self.y - line_len * math.sin(math.radians(-self.angle)) # Y is inverted in pygame
        pygame.draw.line(screen, (0, 255, 0), (int(self.x), int(self.y)), (int(end_x), int(end_y)), 1)