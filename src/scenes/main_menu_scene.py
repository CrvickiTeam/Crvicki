import pygame

from .scene import Scene

class MainMenuScene(Scene):
    """Main menu scene with a button to start the game."""

    def __init__(self, manager, config) -> None:
        super().__init__(manager, config)
        self.font = pygame.font.Font(None, 50)
        self.button_rect = pygame.Rect((self.screen_width // 2 - 100, self.screen_height // 2 - 25), (200, 50))
        self.button_color = (0, 150, 0)
        self.button_text = self.font.render("Start Game", True, (255, 255, 255))
        self.text_rect = self.button_text.get_rect(center=self.button_rect.center)

    def handle_input(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self.button_rect.collidepoint(event.pos):
                    print("Start Game button clicked!")
                    self.manager.switch_scene("GAME")

    def update(self, dt: float) -> None:
        # Can add hover effects here later if needed
        pass

    def draw(self, screen: pygame.Surface) -> None:
        pygame.draw.rect(screen, self.button_color, self.button_rect)
        screen.blit(self.button_text, self.text_rect)