import pygame
import os # Import os for path joining

from .scene import Scene

# Constants for colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
LIGHT_GRAY = (200, 200, 200)
DARK_GRAY = (100, 100, 100)
BUTTON_DISABLED_COLOR = (160, 160, 160) # Color for disabled buttons
LIGHT_GREEN_BACKGROUND = (152, 251, 152) # Light green for background

BUTTON_IDLE_COLOR = (0, 150, 0)
BUTTON_HOVER_COLOR = DARK_GRAY
INFO_BUTTON_IDLE_COLOR = (100, 100, 150) # A different color for info buttons
INFO_BUTTON_HOVER_COLOR = (150, 150, 200)
BUTTON_TEXT_COLOR = WHITE # Text color for better contrast on dark buttons

class MainMenuScene(Scene):
    """Main menu scene with a title and buttons."""

    def __init__(self, manager, config) -> None:
        super().__init__(manager, config)

        # Game settings variables
        self.player_count = 2
        self.game_mode = "FFA"

        # Fonts
        self.title_font = pygame.font.Font(None, 80)
        self.button_font = pygame.font.Font(None, 40) # Adjusted for potentially more text

        # Title - Prepare individual letter surfaces for better kerning
        self.title_text = "Crvicki"
        self.title_letter_surfaces = []
        self.title_letter_rects = []
        title_total_width = 0
        letter_spacing = -5 # Adjust for tighter/looser kerning; negative for tighter

        for char in self.title_text:
            surface = self.title_font.render(char, True, BLACK)
            self.title_letter_surfaces.append(surface)
            title_total_width += surface.get_width() + letter_spacing
        
        title_total_width -= letter_spacing # Remove last spacing

        current_x_offset = (self.screen_width - title_total_width) // 2
        title_y_center = 100

        for surface in self.title_letter_surfaces:
            rect = surface.get_rect(left=current_x_offset, centery=title_y_center)
            self.title_letter_rects.append(rect)
            current_x_offset += surface.get_width() + letter_spacing


        # Load tank image for background
        self.tank_image = None
        try:
            script_dir = os.path.dirname(__file__)
            project_root = os.path.abspath(os.path.join(script_dir, "..", ".."))
            tank_image_path = os.path.join(project_root, "assets", "graphics", "characters", "GREEN-02OPEN-WORM-HAT-TANK.png")
            self.tank_image = pygame.image.load(tank_image_path).convert_alpha()
            self.tank_image = pygame.transform.scale(self.tank_image, (100, 100)) # Adjust size as needed
            self.tank_image_rect = self.tank_image.get_rect(center=(self.screen_width // 2, 180)) # Position below title
        except pygame.error as e:
            print(f"Error loading tank image for main menu: {e}")
            self.tank_image = None


        # Button properties
        button_width = 280 # Increased width for longer text
        button_height = 50
        button_spacing = 15 # Space between buttons
        start_y_offset = 250 # Initial Y position for the first button

        # Start Button
        self.start_button_rect = pygame.Rect(
            (self.screen_width // 2 - button_width // 2, start_y_offset),
            (button_width, button_height)
        )
        self.start_button_idle_color = BUTTON_IDLE_COLOR
        self.start_button_hover_color = BUTTON_HOVER_COLOR
        self.current_start_button_color = self.start_button_idle_color
        self.start_button_text_surface = self.button_font.render("START", True, BUTTON_TEXT_COLOR)
        self.start_button_text_rect = self.start_button_text_surface.get_rect(center=self.start_button_rect.center)

        # Player Count Button
        player_count_button_y = start_y_offset + button_height + button_spacing
        self.player_count_button_rect = pygame.Rect(
            (self.screen_width // 2 - button_width // 2, player_count_button_y),
            (button_width, button_height)
        )
        self.player_count_button_idle_color = INFO_BUTTON_IDLE_COLOR
        self.player_count_button_hover_color = INFO_BUTTON_HOVER_COLOR
        self.current_player_count_button_color = self.player_count_button_idle_color
        self.player_count_text_surface = self.button_font.render(f"Player count: {self.player_count}", True, BUTTON_TEXT_COLOR)
        self.player_count_text_rect = self.player_count_text_surface.get_rect(center=self.player_count_button_rect.center)

        # Game Mode Button
        game_mode_button_y = player_count_button_y + button_height + button_spacing
        self.game_mode_button_rect = pygame.Rect(
            (self.screen_width // 2 - button_width // 2, game_mode_button_y),
            (button_width, button_height)
        )
        self.game_mode_button_idle_color = INFO_BUTTON_IDLE_COLOR
        self.game_mode_button_hover_color = INFO_BUTTON_HOVER_COLOR
        self.current_game_mode_button_color = self.game_mode_button_idle_color
        self.game_mode_text_surface = self.button_font.render(f"Game mode: {self.game_mode}", True, BUTTON_TEXT_COLOR)
        self.game_mode_text_rect = self.game_mode_text_surface.get_rect(center=self.game_mode_button_rect.center)

    def handle_input(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT:
            pygame.quit()
            # Consider sys.exit() or a manager-based quit
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Left mouse button
                if self.start_button_rect.collidepoint(event.pos):
                    print("Start Game button clicked!")
                    # Store the settings in the shared config dictionary
                    # This config is accessible by other scenes, including GameScene.
                    if 'game_settings' not in self.config:
                        self.config['game_settings'] = {}
                    self.config['game_settings']['player_count'] = self.player_count
                    self.config['game_settings']['game_mode'] = self.game_mode
                    
                    print(f"Settings stored in config: {self.config['game_settings']}")
                    
                    self.manager.switch_scene("GAME")
                elif self.player_count_button_rect.collidepoint(event.pos):
                    if self.player_count == 2:
                        self.player_count = 3
                    elif self.player_count == 3:
                        self.player_count = 4
                    elif self.player_count == 4:
                        self.player_count = 2
                    print(f"Player count changed to: {self.player_count}")

                    # If player count is not 4, force game mode to FFA
                    if self.player_count != 4 and self.game_mode == "TEAMS":
                        self.game_mode = "FFA"
                        print(f"Game mode automatically set to FFA due to player count.")

                elif self.game_mode_button_rect.collidepoint(event.pos):
                    # Only allow game mode change if player count is 4
                    if self.player_count == 4:
                        if self.game_mode == "FFA":
                            self.game_mode = "TEAMS"
                        else:
                            self.game_mode = "FFA"
                        print(f"Game mode changed to: {self.game_mode}")
                    else:
                        print("Game mode cannot be changed when player count is not 4.")

    def update(self, dt: float) -> None:
        mouse_pos = pygame.mouse.get_pos()

        # Start Button hover
        if self.start_button_rect.collidepoint(mouse_pos):
            self.current_start_button_color = self.start_button_hover_color
        else:
            self.current_start_button_color = self.start_button_idle_color

        # Player Count Button hover
        if self.player_count_button_rect.collidepoint(mouse_pos):
            self.current_player_count_button_color = self.player_count_button_hover_color
        else:
            self.current_player_count_button_color = self.player_count_button_idle_color

        # Game Mode Button hover and state
        if self.player_count != 4:
            self.current_game_mode_button_color = BUTTON_DISABLED_COLOR
        else:
            if self.game_mode_button_rect.collidepoint(mouse_pos):
                self.current_game_mode_button_color = self.game_mode_button_hover_color
            else:
                self.current_game_mode_button_color = self.game_mode_button_idle_color

        # Update text surfaces if values change
        self.player_count_text_surface = self.button_font.render(f"Player count: {self.player_count}", True, BUTTON_TEXT_COLOR)
        self.player_count_text_rect = self.player_count_text_surface.get_rect(center=self.player_count_button_rect.center)
        self.game_mode_text_surface = self.button_font.render(f"Game mode: {self.game_mode}", True, BUTTON_TEXT_COLOR)
        self.game_mode_text_rect = self.game_mode_text_surface.get_rect(center=self.game_mode_button_rect.center)


    def draw(self, screen: pygame.Surface) -> None:
        screen.fill(LIGHT_GREEN_BACKGROUND) # Use new background color

        # Draw Title letters
        for i, surface in enumerate(self.title_letter_surfaces):
            screen.blit(surface, self.title_letter_rects[i])

        # Draw tank image if loaded
        if self.tank_image:
            screen.blit(self.tank_image, self.tank_image_rect)

        # Draw Start Button
        pygame.draw.rect(screen, self.current_start_button_color, self.start_button_rect, border_radius=8)
        screen.blit(self.start_button_text_surface, self.start_button_text_rect)

        # Draw Player Count Button
        pygame.draw.rect(screen, self.current_player_count_button_color, self.player_count_button_rect, border_radius=8)
        screen.blit(self.player_count_text_surface, self.player_count_text_rect)

        # Draw Game Mode Button
        pygame.draw.rect(screen, self.current_game_mode_button_color, self.game_mode_button_rect, border_radius=8)
        screen.blit(self.game_mode_text_surface, self.game_mode_text_rect)