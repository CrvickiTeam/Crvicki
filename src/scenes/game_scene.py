import pygame

from .scene import Scene

class GameScene(Scene):
    """Game scene where the main gameplay occurs."""

    def __init__(self, manager, config) -> None:
        super().__init__(manager, config)
        # self.font = pygame.font.Font(None, 74) # Keep if needed for UI
        # self.text = self.font.render("Game Screen", True, (200, 200, 200))
        # self.text_rect = self.text.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
        self.game_controller = self.manager.game_controller
        # REMOVE: self.last_dt = 0.0 # No longer needed

    def handle_input(self, event: pygame.event.Event) -> None:
        """Handles discrete input events like key presses (not holds) and mouse clicks."""
        # active_player = self.game_controller.get_active_player() # Get player if needed for non-movement actions

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.manager.switch_scene("MAIN_MENU")
            elif event.key == pygame.K_TAB: # Example: Use Tab to switch turns
                self.game_controller.next_turn()

            # --- REMOVE Movement handling from KEYDOWN ---
            # if active_player:
            #     if event.key == pygame.K_LEFT:
            #         pass # Movement handled in update
            #     elif event.key == pygame.K_RIGHT:
            #         pass # Movement handled in update
            #     # Handle single-press actions like jump or fire here
            #     # elif event.key == pygame.K_UP:
            #     #     active_player.jump()
            #     # elif event.key == pygame.K_SPACE:
            #     #     active_player.fire_weapon()

        elif event.type == pygame.MOUSEBUTTONDOWN:
             if event.button == 1: # Left click for explosion (testing)
                 x, y = event.pos
                 self.game_controller.explode(x, y)

    def update(self, dt: float) -> None:
        """Checks for held keys and updates game logic."""
        # --- Handle continuous input (key holds) ---
        keys = pygame.key.get_pressed()
        active_player = self.game_controller.get_active_player()

        if active_player:
            if keys[pygame.K_LEFT]:
                active_player.move_left(dt) # Pass dt directly
            if keys[pygame.K_RIGHT]:
                active_player.move_right(dt) # Pass dt directly

        # --- Update game state via controller ---
        self.game_controller.update(dt) # Call controller's update

    def draw(self, screen: pygame.Surface) -> None:
        """Draws the game scene by calling the game controller's draw method."""
        # Optional: Fill background if controller doesn't handle it
        screen.fill((100, 160, 255)) # Example sky blue
        self.game_controller.draw_components(screen)
        # Draw any scene-specific UI on top if needed
        # screen.blit(self.text, self.text_rect)
