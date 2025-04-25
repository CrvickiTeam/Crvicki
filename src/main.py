import pygame
from scene_manager import SceneManager

def main() -> None:
    pygame.init()
    screen_width = 800
    screen_height = 600
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Crvicki Game")

    manager = SceneManager("MAIN_MENU", screen)
    manager.run()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"An error occurred: {e}")