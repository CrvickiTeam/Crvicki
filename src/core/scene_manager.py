from __future__ import annotations
import pygame

from scenes.scene import Scene
from scenes.main_menu_scene import MainMenuScene
from scenes.game_scene import GameScene # Make sure GameScene is imported
from scenes.pause_menu_scene import PauseMenuScene
from scenes.win_menu_scene import WinMenuScene
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
            "GAME": GameScene(self, config), # GameScene is instantiated here
            "PAUSE_MENU": PauseMenuScene(self, config),
            "WIN_MENU": WinMenuScene(self, config),
        }
        if initial_scene_name not in self.scenes:
            raise ValueError(f"Initial scene '{initial_scene_name}' not found.")

        self.active_scene_key = initial_scene_name # Initialize active_scene_key
        self.active_scene = self.scenes[initial_scene_name]
        self.game_paused_by_menu = False # Track if the game was paused by the menu


    def switch_scene(self, new_scene_key: str) -> None:
        if new_scene_key == "QUIT": # This signal can be used by the main loop
            pygame.event.post(pygame.event.Event(pygame.QUIT))
            return

        if new_scene_key == "RESUME_GAME":
            if self.active_scene_key == "PAUSE_MENU":
                self.active_scene_key = "GAME"
                self.active_scene = self.scenes["GAME"]
                self.game_paused_by_menu = False
            return

        if new_scene_key not in self.scenes:
            print(f"Warning: Scene '{new_scene_key}' not found!")
            return
        
        # Logic before switching
        if new_scene_key == "PAUSE_MENU":
            if self.active_scene_key == "GAME":
                self.game_paused_by_menu = True
            else:
                print("Warning: Can only pause from GAME scene.")
                return # Don't switch if not in game
        elif new_scene_key == "GAME": # Intending to go to Game scene (e.g. from Main Menu or Win Menu)
            self.active_scene = self.scenes["GAME"] # Set active scene before starting game
            self.game_controller.start_new_game(TerrainMap.FLAT)
            # Reset GameScene specific states, like the timer
            game_scene_instance = self.scenes.get("GAME")
            if isinstance(game_scene_instance, GameScene): # Type check for safety
                game_scene_instance.reset_timer() # Call the new reset method
            self.game_paused_by_menu = False
        elif new_scene_key == "MAIN_MENU":
            self.game_paused_by_menu = False # Reset pause state
            # If coming from game, game_controller state persists until a new game is started via "GAME" scene.

        # Actual switch
        self.active_scene_key = new_scene_key
        self.active_scene = self.scenes[self.active_scene_key]

    def update_active_scene(self, dt: float) -> None:
        # Update logic based on current scene and pause state
        if self.active_scene_key == "GAME":
            if not self.game_paused_by_menu: # Game logic updates if not paused
                self.scenes["GAME"].update(dt)
            # If game is over (WIN_MENU active), game_controller.running is False, so GAME update is minimal.
        elif self.active_scene_key == "PAUSE_MENU":
            self.scenes["PAUSE_MENU"].update(dt) # Pause menu updates its own state
        elif self.active_scene_key == "WIN_MENU":
            self.scenes["WIN_MENU"].update(dt) # Win menu updates its own state (e.g., button hover)
        else: # For other scenes like MAIN_MENU
            self.active_scene.update(dt)

        # Drawing logic
        if self.active_scene_key == "PAUSE_MENU":
            self.scenes["GAME"].draw(self.screen)      # Draw the underlying game screen (frozen)
            self.scenes["PAUSE_MENU"].draw(self.screen) # Draw the pause menu on top
        elif self.active_scene_key == "WIN_MENU": 
            self.scenes["GAME"].draw(self.screen)      # Draw the underlying game screen (frozen)
            self.scenes["WIN_MENU"].draw(self.screen) # Draw the win menu on top
        else:
            # For GAME, MAIN_MENU, etc., they handle their own full draw, including background
            self.active_scene.draw(self.screen)


    def handle_active_scene_input(self, event: pygame.event.Event) -> None:
        self.active_scene.handle_input(event)