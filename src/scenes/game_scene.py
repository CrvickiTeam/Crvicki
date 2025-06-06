import pygame
from typing import Optional 

from .scene import Scene
from core.game_manager import GameManager # TurnStage removed from import
from core.player import Player 

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
            self.font: pygame.font.Font = pygame.font.Font(None, 36)
        except pygame.error:
            print("Warning: Default font not found. Using fallback.")
            self.font = pygame.font.SysFont("arial", 36)
        self.game_time_seconds: float = 0.0
        self.text_color: tuple[int, int, int] = (255, 255, 255)

    def reset_timer(self) -> None:
        self.game_time_seconds = 0.0
        print("Game timer reset.")

    def handle_input(self, event: pygame.event.Event) -> None:
        active_player: Optional[Player] = self.game_controller.get_active_player()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.manager.switch_scene("PAUSE_MENU")
            elif event.key == pygame.K_SPACE:
                if active_player: # Ensure there's an active player
                    # if self.game_controller.current_turn_stage == TurnStage.MOVING: # REMOVE
                    #     self.game_controller.switch_to_aiming_stage() # REMOVE
                    # elif self.game_controller.current_turn_stage == TurnStage.AIMING: # REMOVE
                    angle, power = active_player.get_shot_info()
                    # Use a default weapon ID or implement weapon selection
                    self.game_controller.execute_player_action("basic_cannon", angle, power) 

    def update(self, dt: float) -> None:
        keys: pygame.key.ScancodeWrapper = pygame.key.get_pressed() 
        
        if self.game_controller.running:
            self.game_time_seconds += dt 

            for player in self.game_controller.players:
                if player.alive and self.game_controller.terrain: 
                    player.update(dt, self.game_controller.terrain)

            active_player: Optional[Player] = self.game_controller.get_active_player()
            if active_player and not self.game_controller.active_weapon: 
                
                moved_this_frame_input = False # Track if A or D was pressed this frame
                if keys[pygame.K_a]:
                    active_player.move_left()
                    moved_this_frame_input = True
                elif keys[pygame.K_d]: 
                    active_player.move_right()
                    moved_this_frame_input = True
                
                if not moved_this_frame_input: # If neither A nor D is pressed
                    active_player.stop_moving() # Tell the player to stop
                
                # Aiming input
                if keys[pygame.K_LEFT]: active_player.aim_up(dt)
                elif keys[pygame.K_RIGHT]: active_player.aim_down(dt)
                
                if keys[pygame.K_UP]: active_player.increase_power(dt)
                elif keys[pygame.K_DOWN]: active_player.decrease_power(dt)
        
        game_status: Optional[str] = self.game_controller.update(dt)

        if game_status == "GAME_OVER":
            print("GameScene: Detected GAME_OVER, switching to WIN_MENU.")
            self.manager.switch_scene("WIN_MENU")

    def draw(self, screen: pygame.Surface) -> None:
        screen.fill(self.sky_color) 
        self.game_controller.draw_components(screen)

        if not self.font: 
            return

        minutes: int = int(self.game_time_seconds // 60)
        seconds: int = int(self.game_time_seconds % 60)
        timer_text_str: str = f"{minutes:02d}:{seconds:02d}"
        timer_surface: pygame.Surface = self.font.render(timer_text_str, True, self.text_color)
        timer_rect: pygame.Rect = timer_surface.get_rect(center=(screen.get_width() // 2, 30))
        screen.blit(timer_surface, timer_rect)

        active_player_display_index: int = self.game_controller.current_player_index + 1
        player_turn_text_str: str = f"Player {active_player_display_index}'s turn"
        player_turn_surface: pygame.Surface = self.font.render(player_turn_text_str, True, self.text_color)
        player_turn_rect: pygame.Rect = player_turn_surface.get_rect(topleft=(20, 20))
        screen.blit(player_turn_surface, player_turn_rect)

        # stage_text_str: str = "" # REMOVE STAGE DISPLAY
        # if self.game_controller.current_turn_stage == TurnStage.MOVING:
        #     stage_text_str = "Moving stage"
        # elif self.game_controller.current_turn_stage == TurnStage.AIMING:
        #     stage_text_str = "Shooting stage"
        
        # if stage_text_str:
        #     stage_surface: pygame.Surface = self.font.render(stage_text_str, True, self.text_color)
        #     stage_rect: pygame.Rect = stage_surface.get_rect(topleft=(20, player_turn_rect.bottom + 5))
        #     screen.blit(stage_surface, stage_rect)
