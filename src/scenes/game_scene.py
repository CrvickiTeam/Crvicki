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
                self.game_controller.next_turn()
            elif event.key == pygame.K_SPACE:
                if active_player:
                    angle, power = active_player.get_shot_info()
                    self.game_controller.prepare_shot(angle, power)

    def update(self, dt: float) -> None:
        keys = pygame.key.get_pressed()
        
        if self.game_controller.running:
            # Update all players' physics and state
            for player in self.game_controller.players:
                if player.alive: # Only update alive players
                    player.update(dt, self.game_controller.terrain)

            # Handle input for the active player
            active_player = self.game_controller.get_active_player()
            if active_player: # active_player is already checked for being alive by get_active_player
                if not self.game_controller.active_weapon: # Only allow player input if no weapon is active
                    if keys[pygame.K_a]:
                        active_player.move_left()
                    if keys[pygame.K_d]:
                        active_player.move_right()

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
            print("GameScene: Detected GAME_OVER, switching to MAIN_MENU.")
            self.manager.switch_scene("MAIN_MENU")

    def draw(self, screen: pygame.Surface) -> None:
        screen.fill((100, 160, 255))
        self.game_controller.draw_components(screen)
