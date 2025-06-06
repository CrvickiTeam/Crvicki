import pygame

from .scene import Scene

class GameScene(Scene):
    """Game scene where the main gameplay occurs."""

    def __init__(self, manager, config) -> None:
        super().__init__(manager, config)
        background_config = self.config.get("game", {}).get("background", {})
        self.sky_color = background_config.get("sky_color", (100, 160, 255))
        self.enable_clouds = background_config.get("enable_clouds", True)    

        self.game_controller = self.manager.game_controller
         

    def handle_input(self, event: pygame.event.Event) -> None:
        active_player = self.game_controller.get_active_player()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.manager.switch_scene("PAUSE_MENU")
            elif event.key == pygame.K_TAB:
                # Only allow next_turn if no weapon is active (player is in control)
                if active_player and not self.game_controller.active_weapon:
                    self.game_controller.next_turn()
            elif event.key == pygame.K_SPACE:
                # Only allow firing if no weapon is active and there's an active player
                if active_player and not self.game_controller.active_weapon:
                    angle, power = active_player.get_shot_info()
                    # Call the updated GameManager method, hardcoding "basic_cannon" for now
                    self.game_controller.execute_player_action("basic_cannon", angle, power)

    def update(self, dt: float) -> None:
        keys = pygame.key.get_pressed()
        
        if self.game_controller.running:
            # Update all players' physics and state
            # This loop ensures all players are affected by gravity, etc.
            for player in self.game_controller.players:
                if player.alive: # Only update alive players
                    player.update(dt, self.game_controller.terrain)

            # Handle input for the active player's movement and aiming
            active_player = self.game_controller.get_active_player()
            if active_player: 
                # Only allow player input if no weapon is active (i.e., player is in aiming phase)
                if not self.game_controller.active_weapon: 
                    if keys[pygame.K_a]:
                        active_player.move_left()
                    if keys[pygame.K_d]:
                        active_player.move_right()

                    if keys[pygame.K_LEFT]: # Aiming keys
                        active_player.aim_up(dt)
                    if keys[pygame.K_RIGHT]:
                        active_player.aim_down(dt)
                    if keys[pygame.K_DOWN]: # In your setup, this was decrease_power
                        active_player.decrease_power(dt)
                    if keys[pygame.K_UP]: # And this was increase_power
                        active_player.increase_power(dt)
        
        # Update game controller (handles active weapon logic, turn progression, game over checks)
        game_status = self.game_controller.update(dt)

        if game_status == "GAME_OVER":
            print("GameScene: Detected GAME_OVER, switching to MAIN_MENU.")
            # Consider a dedicated game over scene instead of directly to main menu
            self.manager.switch_scene("MAIN_MENU") 

    def draw(self, screen: pygame.Surface) -> None:
        screen.fill(self.sky_color) # Use configured sky color
        # Add cloud drawing logic here if self.enable_clouds is True

        self.game_controller.draw_components(screen)
