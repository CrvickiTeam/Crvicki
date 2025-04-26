import pygame

from .scene import Scene

class GameScene(Scene):
    """Game scene where the main gameplay occurs."""

    def __init__(self, manager, config) -> None:
        super().__init__(manager, config)
        self.game_controller = self.manager.game_controller

    def handle_input(self, event: pygame.event.Event) -> None:
        """Handles discrete input events like key presses (not holds) and mouse clicks."""
        active_player = self.game_controller.get_active_player()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.manager.switch_scene("MAIN_MENU")
            elif event.key == pygame.K_TAB:
                self.game_controller.next_turn()
            # --- Handle Firing ---
            elif event.key == pygame.K_SPACE:
                if active_player:
                    angle, power = active_player.get_shot_info()
                    # Pass info to game controller to handle projectile creation/firing
                    self.game_controller.prepare_shot(angle, power)
                    # Optionally switch turn immediately after firing attempt
                    # self.game_controller.next_turn()

        elif event.type == pygame.MOUSEBUTTONDOWN:
             if event.button == 1: # Left click for explosion (testing)
                 x, y = event.pos
                 self.game_controller.explode(x, y)

    def update(self, dt: float) -> None:
        """Checks for held keys and updates game logic."""
        keys = pygame.key.get_pressed()
        active_player = self.game_controller.get_active_player()

        if active_player:
            # --- Movement ---
            if keys[pygame.K_a]: # Use A for left
                active_player.move_left()
            if keys[pygame.K_d]: # Use D for right
                active_player.move_right()

            # --- Aiming ---
            if keys[pygame.K_LEFT]:
                active_player.aim_up(dt)
            if keys[pygame.K_RIGHT]:
                active_player.aim_down(dt)
            if keys[pygame.K_DOWN]: # Use Left Arrow for power down
                active_player.decrease_power(dt)
            if keys[pygame.K_UP]: # Use Right Arrow for power up
                active_player.increase_power(dt)

        # Update game state via controller
        self.game_controller.update(dt)

    def draw(self, screen: pygame.Surface) -> None:
        """Draws the game scene by calling the game controller's draw method."""
        screen.fill((100, 160, 255)) # Example sky blue
        self.game_controller.draw_components(screen)
