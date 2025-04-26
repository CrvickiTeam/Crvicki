import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

import pygame
import json 

from core.scene_manager import SceneManager
from core.game_manager import GameManager

CONFIG = {
    "display": {
        "width": 1280,
        "height": 720,
        "caption": "Crvicki Game",
        "fps_limit": 60
    }
}


def main() -> None:
    config = CONFIG
    display_config: dict = config.get("display", {})
    screen_width: int = display_config.get("width", 800)
    screen_height: int = display_config.get("height", 600)
    screen_title: str = display_config.get("title", "Crvicki Game")
    fps_limit: int = display_config.get("fps_limit", 60)

    pygame.init()
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption(screen_title)

    game_controller = GameManager(config)
    scene_manager = SceneManager("MAIN_MENU", screen, game_controller, config)

    
    clock = pygame.time.Clock()
    running = True
    while running:
        dt = clock.tick(fps_limit) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            scene_manager.handle_active_scene_input(event)
        scene_manager.update_active_scene(dt)
        pygame.display.flip()
        
    pygame.quit()
    print("Game exited gracefully.")


if __name__ == "__main__":
    main()