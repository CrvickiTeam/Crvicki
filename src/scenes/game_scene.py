import pygame
from typing import Optional 

from .scene import Scene
from core.game_manager import GameManager 
from core.player import Player 
from core.weapons.weapon import WeaponType, WEAPON_TYPES_ORDERED # <<< IMPORT WeaponType

class GameScene(Scene):
    """Game scene where the main gameplay occurs."""

    def __init__(self, manager, config: dict) -> None: # Added type hint for config
        super().__init__(manager, config)
        background_config: dict = self.config.get("game", {}).get("background", {})
        self.sky_color: tuple[int, int, int] = background_config.get("sky_color", (100, 160, 255))
        # self.enable_clouds = background_config.get("enable_clouds", True) # Not used in current snippet

        # Assuming self.manager.game_controller is an instance of GameManager
        self.game_controller: GameManager = self.manager.game_controller 
        
        try:
            self.font: pygame.font.Font = pygame.font.Font(None, 30) # Slightly smaller for inventory
            self.ui_font: pygame.font.Font = pygame.font.Font(None, 24) # For weapon names/ammo
        except pygame.error:
            print("Warning: Default font not found. Using fallback.")
            self.font = pygame.font.SysFont("arial", 30)
            self.ui_font = pygame.font.SysFont("arial", 24)
        self.game_time_seconds: float = 0.0
        self.text_color: tuple[int, int, int] = (255, 255, 255)
        self.selected_weapon_color: tuple[int, int, int] = (255, 255, 0) # Yellow
        self.disabled_weapon_color: tuple[int, int, int] = (100, 100, 100) # Grey

    def reset_timer(self) -> None:
        self.game_time_seconds = 0.0
        print("Game timer reset.")

    def handle_input(self, event: pygame.event.Event) -> None:
        active_player: Optional[Player] = self.game_controller.get_active_player()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.manager.switch_scene("PAUSE_MENU")
            elif active_player and not self.game_controller.active_weapon: # Only allow actions if it's player's turn and no weapon active
                if event.key == pygame.K_SPACE:
                    selected_weapon = active_player.get_selected_weapon_type()
                    # Player.consume_selected_weapon now returns bool if fireable
                    if active_player.consume_selected_weapon(): 
                        angle, power = active_player.get_shot_info()
                        self.game_controller.execute_player_action(selected_weapon, angle, power)
                elif event.key == pygame.K_1:
                    active_player.select_weapon_by_index(0)
                elif event.key == pygame.K_2:
                    active_player.select_weapon_by_index(1)
                elif event.key == pygame.K_3:
                    active_player.select_weapon_by_index(2)
                elif event.key == pygame.K_4:
                    active_player.select_weapon_by_index(3)
                # Add K_5, K_6 etc. if more weapons

    def update(self, dt: float) -> None:
        keys: pygame.key.ScancodeWrapper = pygame.key.get_pressed() 
        
        if self.game_controller.running:
            self.game_time_seconds += dt 

            for player in self.game_controller.players:
                if player.alive and self.game_controller.terrain: 
                    player.update(dt, self.game_controller.terrain)

            active_player: Optional[Player] = self.game_controller.get_active_player()
            if active_player and not self.game_controller.active_weapon: 
                
                moved_this_frame_input = False 
                if keys[pygame.K_a]:
                    active_player.move_left()
                    moved_this_frame_input = True
                elif keys[pygame.K_d]: 
                    active_player.move_right()
                    moved_this_frame_input = True
                
                if not moved_this_frame_input: 
                    active_player.stop_moving() 
                
                # --- Modified Aiming Logic ---
                if keys[pygame.K_LEFT]: # Pressing "left arrow" key
                    if active_player.direction == 1: # Player is facing right
                        active_player.aim_up(dt) # Decrease angle (aims "up" or counter-clockwise)
                    else: # Player is facing left (direction == -1)
                        active_player.aim_down(dt) # Increase angle (aims "down" or clockwise, relative to player)
                elif keys[pygame.K_RIGHT]: # Pressing "right arrow" key
                    if active_player.direction == 1: # Player is facing right
                        active_player.aim_down(dt) # Increase angle (aims "down" or clockwise)
                    else: # Player is facing left (direction == -1)
                        active_player.aim_up(dt) # Decrease angle (aims "up" or counter-clockwise, relative to player)
                # --- End Modified Aiming Logic ---
                
                if keys[pygame.K_UP]: active_player.increase_power(dt)
                elif keys[pygame.K_DOWN]: active_player.decrease_power(dt)
        
        game_status: Optional[str] = self.game_controller.update(dt)

        if game_status == "GAME_OVER":
            print("GameScene: Detected GAME_OVER, switching to WIN_MENU.")
            self.manager.switch_scene("WIN_MENU")
    
    def _draw_inventory_ui(self, screen: pygame.Surface, active_player: Optional[Player]) -> None:
        if not active_player or not self.ui_font:
            return

        start_x = 20
        start_y = 60 # Below player turn text
        line_height = 25
        
        for i, weapon_type in enumerate(WEAPON_TYPES_ORDERED):
            name = f"{i+1}. {weapon_type.display_name()}"
            quantity_str = active_player.get_weapon_quantity_display(weapon_type)
            text = f"{name}: {quantity_str}"
            
            color = self.text_color
            if active_player.get_selected_weapon_type() == weapon_type:
                color = self.selected_weapon_color
            elif active_player.get_weapon_quantity(weapon_type) == 0: # Not -1 (infinite)
                color = self.disabled_weapon_color
            
            text_surface = self.ui_font.render(text, True, color)
            screen.blit(text_surface, (start_x, start_y + i * line_height))

    def draw(self, screen: pygame.Surface) -> None:
        screen.fill(self.sky_color) 
        self.game_controller.draw_components(screen)

        if not self.font: 
            return

        # Timer
        minutes: int = int(self.game_time_seconds // 60)
        seconds: int = int(self.game_time_seconds % 60)
        timer_text_str: str = f"{minutes:02d}:{seconds:02d}"
        timer_surface: pygame.Surface = self.font.render(timer_text_str, True, self.text_color)
        timer_rect: pygame.Rect = timer_surface.get_rect(center=(screen.get_width() // 2, 30))
        screen.blit(timer_surface, timer_rect)

        # Player Turn
        active_player_display_index: int = self.game_controller.current_player_index + 1
        player_turn_text_str: str = f"Player {active_player_display_index}'s turn"
        player_turn_surface: pygame.Surface = self.font.render(player_turn_text_str, True, self.text_color)
        player_turn_rect: pygame.Rect = player_turn_surface.get_rect(topleft=(20, 20))
        screen.blit(player_turn_surface, player_turn_rect)

        # Inventory UI
        active_player: Optional[Player] = self.game_controller.get_active_player()
        if active_player and not self.game_controller.active_weapon: # Show inventory only during player's control phase
            self._draw_inventory_ui(screen, active_player)
