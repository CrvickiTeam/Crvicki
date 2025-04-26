import pygame

from .scene import Scene

class GameScene(Scene):
    """Game scene where the main gameplay occurs."""

    def __init__(self, manager, config) -> None:
        super().__init__(manager, config)
        self.font = pygame.font.Font(None, 74)
        self.text = self.font.render("Game Screen", True, (200, 200, 200))
        self.text_rect = self.text.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
        self.game_controller = self.manager.game_controller

    def handle_input(self, event: pygame.event.Event) -> None:
        """Handles input for the game scene."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.manager.switch_scene("MAIN_MENU")
        # --- Handle player input, weapon firing etc. ---
        # Example: Simulate explosion on mouse click
        if event.type == pygame.MOUSEBUTTONDOWN:
             if event.button == 1: # Left click
                 x, y = event.pos
                 self.game_controller.explode(x, y)


    def update(self, dt: float) -> None:
        """Updates game logic (physics, AI, etc.)."""
        pass

    def draw(self, screen: pygame.Surface) -> None:
        screen.fill((100, 160, 255))
        self.game_controller.draw_components(screen)