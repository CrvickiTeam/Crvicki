import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

import pygame
import json 

from core.scene_manager import SceneManager
from core.game_manager import GameManager

from typing import Dict, Any


def load_config(file_path: str) -> Dict[str, Any]:
    """Load the game configuration from a JSON file."""
    try:
        with open(file_path, 'r') as file:
            config = json.load(file)
        return config
    except FileNotFoundError:
        print(f"Error: Configuration file '{file_path}' not found.")
        return {}
    except json.JSONDecodeError:
        print(f"Error: Configuration file '{file_path}' is not a valid JSON.")
        return {}
    except Exception as e:
        print(f"Error loading configuration: {e}")
        return {}


def main() -> None:
    config = load_config("src/config.json")
    display_config: dict = config.get("display", {})
    screen_width: int = display_config.get("width", 1280)
    screen_height: int = display_config.get("height", 720)
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