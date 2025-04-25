import pygame

from .scene import Scene

class GameScene(Scene):
    """Game scene where the main gameplay occurs."""

    def __init__(self, manager) -> None:
        super().__init__(manager)
        self.font = pygame.font.Font(None, 74)
        self.text = self.font.render("Game Screen", True, (200, 200, 200))
        self.text_rect = self.text.get_rect(center=(400, 300))

    def handle_input(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.manager.switch_scene("MAIN_MENU")

    def update(self, dt: float) -> None:
        pass

    def draw(self, screen: pygame.Surface) -> None:
        screen.fill((50, 50, 100))
        screen.blit(self.text, self.text_rect)