import pygame

from .scene import Scene

# Constants for colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
LIGHT_GRAY = (200, 200, 200)
DARK_GRAY = (100, 100, 100)

BUTTON_IDLE_COLOR = (0, 150, 0) 
BUTTON_HOVER_COLOR = DARK_GRAY

class MainMenuScene(Scene):
    """Main menu scene with a title and a button to start the game."""

    def __init__(self, manager, config) -> None:
        super().__init__(manager, config)

        # Fonts
        self.title_font = pygame.font.Font(None, 80) # Adjusted font size for title
        self.button_font = pygame.font.Font(None, 50) # Font for the button text

        # Title
        self.title_text_surface = self.title_font.render("Crvicki", True, BLACK)
        # Position title: center of screen_width, 100 pixels from the top
        self.title_text_rect = self.title_text_surface.get_rect(center=(self.screen_width // 2, 100))

        # Start Button
        # Using dimensions and y-position from your example: Rect(center_x - 100, 300, 200, 60)
        button_width = 200
        button_height = 60
        # Centered horizontally, at y=300
        self.button_rect = pygame.Rect(
            (self.screen_width // 2 - button_width // 2, 300),
            (button_width, button_height)
        )
        self.button_idle_color = BUTTON_IDLE_COLOR 
        self.button_hover_color = BUTTON_HOVER_COLOR
        self.current_button_color = self.button_idle_color # Initial color
        
        self.button_text_surface = self.button_font.render("START", True, BLACK) # Text color BLACK
        self.button_text_rect = self.button_text_surface.get_rect(center=self.button_rect.center)

    def handle_input(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT: # Basic quit event, usually handled by main loop
            pygame.quit()
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Left mouse button
                if self.button_rect.collidepoint(event.pos):
                    print("Start Game button clicked!")
                    # Assuming screen resizing is handled by the scene manager or game scene
                    self.manager.switch_scene("GAME")

    def update(self, dt: float) -> None:
        mouse_pos = pygame.mouse.get_pos()
        if self.button_rect.collidepoint(mouse_pos):
            self.current_button_color = self.button_hover_color
        else:
            self.current_button_color = self.button_idle_color

    def draw(self, screen: pygame.Surface) -> None:
        screen.fill(WHITE) # Fill screen with white background

        # Draw Title
        screen.blit(self.title_text_surface, self.title_text_rect)

        # Draw Start Button
        pygame.draw.rect(screen, self.current_button_color, self.button_rect, border_radius=8)
        screen.blit(self.button_text_surface, self.button_text_rect)