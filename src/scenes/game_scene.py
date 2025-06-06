import pygame

from .scene import Scene
from core.game_manager import TurnStage # Import TurnStage

class GameScene(Scene):
    """Game scene where the main gameplay occurs."""

    def __init__(self, manager, config) -> None:
        super().__init__(manager, config)
        background_config = self.config.get("game", {}).get("background", {})
        self.sky_color = background_config.get("sky_color", (100, 160, 255))
        self.enable_clouds = background_config.get("enable_clouds", True)    

        self.game_controller = self.manager.game_controller
        
        # Initialize font and timer
        try:
            self.font = pygame.font.Font(None, 36) # Default system font, size 36
        except pygame.error:
            print("Warning: Default font not found. Using fallback.")
            self.font = pygame.font.SysFont("arial", 36) # Fallback
        self.game_time_seconds = 0.0
        self.text_color = (255, 255, 255) # White color for text

    def handle_input(self, event: pygame.event.Event) -> None:
        active_player = self.game_controller.get_active_player()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.manager.switch_scene("PAUSE_MENU")
            elif event.key == pygame.K_TAB:
                # Potentially disable manual turn switching or make it conditional
                # For now, let's assume it's for debugging or a specific mechanic
                # If it's meant to end the current stage and move to next player,
                # this logic would need to be more complex (e.g., force end turn).
                # self.game_controller.next_turn() # Original behavior
                pass # K_TAB might be used differently now or disabled during normal play
            elif event.key == pygame.K_SPACE:
                if active_player:
                    if self.game_controller.current_turn_stage == TurnStage.MOVING:
                        self.game_controller.switch_to_aiming_stage()
                    elif self.game_controller.current_turn_stage == TurnStage.AIMING:
                        angle, power = active_player.get_shot_info()
                        self.game_controller.prepare_shot(angle, power)

    def update(self, dt: float) -> None:
        keys = pygame.key.get_pressed()
        
        if self.game_controller.running:
            self.game_time_seconds += dt # Increment game timer

            # Update all players' physics and state
            for player in self.game_controller.players:
                if player.alive: # Only update alive players
                    player.update(dt, self.game_controller.terrain)

            # Handle input for the active player
            active_player = self.game_controller.get_active_player()
            if active_player: # active_player is already checked for being alive by get_active_player
                if not self.game_controller.active_weapon: # Only allow player input if no weapon is active
                    
                    if self.game_controller.current_turn_stage == TurnStage.MOVING:
                        if active_player.distance_moved_this_turn < active_player.max_move_distance_per_turn:
                            if keys[pygame.K_a]:
                                active_player.move_left()
                            if keys[pygame.K_d]:
                                active_player.move_right()
                        else:
                            # If max distance reached, ensure player stops and switch stage (handled in GameManager.update too)
                            active_player.stop_moving()
                            if self.game_controller.current_turn_stage == TurnStage.MOVING: # Double check
                                self.game_controller.switch_to_aiming_stage()
                    
                    elif self.game_controller.current_turn_stage == TurnStage.AIMING:
                        if keys[pygame.K_LEFT]: # Aiming keys
                            active_player.aim_up(dt)
                        if keys[pygame.K_RIGHT]:
                            active_player.aim_down(dt)
                        if keys[pygame.K_DOWN]:
                            active_player.decrease_power(dt)
                        if keys[pygame.K_UP]:
                            active_player.increase_power(dt)
        
        # Update game controller (handles weapons, turns, game over checks)
        game_status = self.game_controller.update(dt)

        if game_status == "GAME_OVER":
            print("GameScene: Detected GAME_OVER, switching to WIN_MENU.")
            self.manager.switch_scene("WIN_MENU")

    def draw(self, screen: pygame.Surface) -> None:
        screen.fill(self.sky_color) # Use configured sky color
        self.game_controller.draw_components(screen)

        if not self.font: # Should not happen if initialized correctly
            return

        # 1. Game Timer (Top-Center)
        minutes = int(self.game_time_seconds // 60)
        seconds = int(self.game_time_seconds % 60)
        timer_text_str = f"{minutes:02d}:{seconds:02d}"
        timer_surface = self.font.render(timer_text_str, True, self.text_color)
        timer_rect = timer_surface.get_rect(center=(screen.get_width() // 2, 30))
        screen.blit(timer_surface, timer_rect)

        # 2. Player Turn Indicator (Top-Left)
        active_player_display_index = self.game_controller.current_player_index + 1
        player_turn_text_str = f"Player {active_player_display_index}'s turn"
        player_turn_surface = self.font.render(player_turn_text_str, True, self.text_color)
        player_turn_rect = player_turn_surface.get_rect(topleft=(20, 20))
        screen.blit(player_turn_surface, player_turn_rect)

        # 3. Turn Stage Indicator (Below Player Turn)
        stage_text_str = ""
        if self.game_controller.current_turn_stage == TurnStage.MOVING:
            stage_text_str = "Moving stage"
        elif self.game_controller.current_turn_stage == TurnStage.AIMING:
            stage_text_str = "Shooting stage"
        
        if stage_text_str:
            stage_surface = self.font.render(stage_text_str, True, self.text_color)
            stage_rect = stage_surface.get_rect(topleft=(20, player_turn_rect.bottom + 5))
            screen.blit(stage_surface, stage_rect)
