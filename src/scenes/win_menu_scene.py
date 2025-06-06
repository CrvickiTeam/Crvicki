import pygame

from .scene import Scene
from core.player import PlayerTeam # For accessing PlayerTeam.value

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
LIGHT_GRAY = (200, 200, 200)
DARK_GRAY = (100, 100, 100)

BUTTON_PLAY_AGAIN_IDLE_COLOR = (0, 150, 0)
BUTTON_PLAY_AGAIN_HOVER_COLOR = (0, 100, 0)
BUTTON_MAIN_MENU_IDLE_COLOR = (150, 0, 0)
BUTTON_MAIN_MENU_HOVER_COLOR = (100, 0, 0)
BUTTON_TEXT_COLOR = WHITE
OVERLAY_COLOR = (0, 0, 0, 180) # Semi-transparent black

class WinMenuScene(Scene):
    """Win menu scene that overlays the game when a player wins."""

    def __init__(self, manager, config) -> None:
        super().__init__(manager, config)

        # Fonts
        self.title_font = pygame.font.Font(None, 70)
        self.button_font = pygame.font.Font(None, 40)

        # Title text surface will be created dynamically in the draw method
        self.title_text_surface = None
        self.title_text_rect = None

        # Button properties
        button_width = 220
        button_height = 50
        button_spacing = 20
        start_y_offset = self.screen_height // 2 - button_height // 2 # Center first button vertically

        # Play Again Button
        self.play_again_button_rect = pygame.Rect(
            (self.screen_width // 2 - button_width // 2, start_y_offset),
            (button_width, button_height)
        )
        self.current_play_again_button_color = BUTTON_PLAY_AGAIN_IDLE_COLOR
        self.play_again_button_text_surface = self.button_font.render("Play Again", True, BUTTON_TEXT_COLOR)
        self.play_again_button_text_rect = self.play_again_button_text_surface.get_rect(center=self.play_again_button_rect.center)

        # Main Menu Button
        main_menu_button_y = start_y_offset + button_height + button_spacing
        self.main_menu_button_rect = pygame.Rect(
            (self.screen_width // 2 - button_width // 2, main_menu_button_y),
            (button_width, button_height)
        )
        self.current_main_menu_button_color = BUTTON_MAIN_MENU_IDLE_COLOR
        self.main_menu_button_text_surface = self.button_font.render("Main Menu", True, BUTTON_TEXT_COLOR)
        self.main_menu_button_text_rect = self.main_menu_button_text_surface.get_rect(center=self.main_menu_button_rect.center)

        # Overlay surface
        self.overlay_surface = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        self.overlay_surface.fill(OVERLAY_COLOR)

    def handle_input(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Left mouse button
                if self.play_again_button_rect.collidepoint(event.pos):
                    # Restart the game with current settings
                    self.manager.switch_scene("GAME")
                elif self.main_menu_button_rect.collidepoint(event.pos):
                    self.manager.switch_scene("MAIN_MENU")

    def update(self, dt: float) -> None:
        mouse_pos = pygame.mouse.get_pos()

        # Play Again Button hover
        if self.play_again_button_rect.collidepoint(mouse_pos):
            self.current_play_again_button_color = BUTTON_PLAY_AGAIN_HOVER_COLOR
        else:
            self.current_play_again_button_color = BUTTON_PLAY_AGAIN_IDLE_COLOR

        # Main Menu Button hover
        if self.main_menu_button_rect.collidepoint(mouse_pos):
            self.current_main_menu_button_color = BUTTON_MAIN_MENU_HOVER_COLOR
        else:
            self.current_main_menu_button_color = BUTTON_MAIN_MENU_IDLE_COLOR

    def draw(self, screen: pygame.Surface) -> None:
        # Draw the semi-transparent overlay
        screen.blit(self.overlay_surface, (0, 0))

        # Determine winner and set title
        winner_team = self.manager.game_controller.get_winner_team()
        if winner_team:
            # Assuming PlayerTeam.TEAM_1.value is 1, PlayerTeam.TEAM_2.value is 2, etc.
            title_string = f"Player {winner_team.value} Wins!"
        else:
            # Handle cases like a draw if no winner_team is set
            title_string = "Game Over!" # Or "It's a Draw!"

        self.title_text_surface = self.title_font.render(title_string, True, WHITE)
        self.title_text_rect = self.title_text_surface.get_rect(center=(self.screen_width // 2, self.screen_height // 2 - 100))

        # Draw Title
        screen.blit(self.title_text_surface, self.title_text_rect)

        # Draw Play Again Button
        pygame.draw.rect(screen, self.current_play_again_button_color, self.play_again_button_rect, border_radius=8)
        screen.blit(self.play_again_button_text_surface, self.play_again_button_text_rect)

        # Draw Main Menu Button
        pygame.draw.rect(screen, self.current_main_menu_button_color, self.main_menu_button_rect, border_radius=8)
        screen.blit(self.main_menu_button_text_surface, self.main_menu_button_text_rect)
