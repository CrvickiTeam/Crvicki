from __future__ import annotations
import pygame

from scenes.scene import Scene
from scenes.main_menu_scene import MainMenuScene
from scenes.game_scene import GameScene
from core.terrain import TerrainMap

from typing import Dict, Any, TYPE_CHECKING
if TYPE_CHECKING:
    from core.game_manager import GameManager

class SceneManager:
    def __init__(self, initial_scene_name: str, screen: pygame.Surface, game_controller: GameManager, config: Dict[str, Any]) -> None:
        """
        Initializes the SceneManager with the initial scene and screen.

        Args:
            initial_scene_name: The key of the scene to start with.
            screen: The main Pygame display surface.
            config: The loaded configuration dictionary.
        """

        self.screen = screen
        self.config = config
        self.game_controller = game_controller
        self.scenes: Dict[str, Scene] = {
            "MAIN_MENU": MainMenuScene(self, config),
            "GAME": GameScene(self, config),
        }
        if initial_scene_name not in self.scenes:
            raise ValueError(f"Initial scene '{initial_scene_name}' not found.")

        self.active_scene = self.scenes[initial_scene_name]


    def switch_scene(self, scene_name: str) -> None:
        if scene_name == "QUIT":
            self.running = False
        elif scene_name == "GAME":
            self.active_scene = self.scenes["GAME"]
            self.game_controller.start_new_game(TerrainMap.FLAT)
        elif scene_name in self.scenes:
            self.active_scene = self.scenes[scene_name]
        else:
            print(f"Warning: Scene '{scene_name}' not found!")


    def update_active_scene(self, dt: float) -> None:
        self.active_scene.update(dt)
        self.screen.fill((0, 0, 0))
        self.active_scene.draw(self.screen)

    def handle_active_scene_input(self, event: pygame.event.Event) -> None:
        self.active_scene.handle_input(event)