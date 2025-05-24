import pygame

from .scene import Scene

# Constants for colors (Se Bo sprmenilo)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
LIGHT_GRAY = (200, 200, 200)
DARK_GRAY = (100, 100, 100)

BUTTON_IDLE_COLOR = (0, 150, 0) 
BUTTON_HOVER_COLOR = (0, 100, 0) 
MAIN_MENU_BUTTON_IDLE_COLOR = (150, 0, 0) 
MAIN_MENU_BUTTON_HOVER_COLOR = (100, 0, 0)
BUTTON_TEXT_COLOR = WHITE
OVERLAY_COLOR = (0, 0, 0, 180) 

class PauseMenuScene(Scene):
    """Pause menu scene that overlays the game."""

    def __init__(self, manager, config) -> None:
        super().__init__(manager, config)

        # Fonts
        self.title_font = pygame.font.Font(None, 70)
        self.button_font = pygame.font.Font(None, 40)

        # Title
        self.title_text_surface = self.title_font.render("PAUSED", True, WHITE)
        self.title_text_rect = self.title_text_surface.get_rect(center=(self.screen_width // 2, self.screen_height // 2 - 100))

        # Button properties
        button_width = 220
        button_height = 50
        button_spacing = 20
        start_y_offset = self.screen_height // 2 - button_height // 2 # Center first button vertically

        # Resume Button
        self.resume_button_rect = pygame.Rect(
            (self.screen_width // 2 - button_width // 2, start_y_offset),
            (button_width, button_height)
        )
        self.current_resume_button_color = BUTTON_IDLE_COLOR
        self.resume_button_text_surface = self.button_font.render("Resume", True, BUTTON_TEXT_COLOR)
        self.resume_button_text_rect = self.resume_button_text_surface.get_rect(center=self.resume_button_rect.center)

        # Main Menu Button
        main_menu_button_y = start_y_offset + button_height + button_spacing
        self.main_menu_button_rect = pygame.Rect(
            (self.screen_width // 2 - button_width // 2, main_menu_button_y),
            (button_width, button_height)
        )
        self.current_main_menu_button_color = MAIN_MENU_BUTTON_IDLE_COLOR
        self.main_menu_button_text_surface = self.button_font.render("Main Menu", True, BUTTON_TEXT_COLOR)
        self.main_menu_button_text_rect = self.main_menu_button_text_surface.get_rect(center=self.main_menu_button_rect.center)

        # Overlay surface
        self.overlay_surface = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        self.overlay_surface.fill(OVERLAY_COLOR)


    def handle_input(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Left mouse button
                if self.resume_button_rect.collidepoint(event.pos):
                    self.manager.switch_scene("RESUME_GAME")
                elif self.main_menu_button_rect.collidepoint(event.pos):
                    self.manager.switch_scene("MAIN_MENU")
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE: # Allow Esc to also resume
                self.manager.switch_scene("RESUME_GAME")


    def update(self, dt: float) -> None:
        mouse_pos = pygame.mouse.get_pos()

        # Resume Button hover
        if self.resume_button_rect.collidepoint(mouse_pos):
            self.current_resume_button_color = BUTTON_HOVER_COLOR
        else:
            self.current_resume_button_color = BUTTON_IDLE_COLOR

        # Main Menu Button hover
        if self.main_menu_button_rect.collidepoint(mouse_pos):
            self.current_main_menu_button_color = MAIN_MENU_BUTTON_HOVER_COLOR
        else:
            self.current_main_menu_button_color = MAIN_MENU_BUTTON_IDLE_COLOR


    def draw(self, screen: pygame.Surface) -> None:
        # Draw the semi-transparent overlay
        screen.blit(self.overlay_surface, (0, 0))

        # Draw Title
        screen.blit(self.title_text_surface, self.title_text_rect)

        # Draw Resume Button
        pygame.draw.rect(screen, self.current_resume_button_color, self.resume_button_rect, border_radius=8)
        screen.blit(self.resume_button_text_surface, self.resume_button_text_rect)

        # Draw Main Menu Button
        pygame.draw.rect(screen, self.current_main_menu_button_color, self.main_menu_button_rect, border_radius=8)
        screen.blit(self.main_menu_button_text_surface, self.main_menu_button_text_rect)