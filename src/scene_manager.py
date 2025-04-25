import pygame

from scenes.main_menu_scene import MainMenuScene
from scenes.game_scene import GameScene

class SceneManager:
    """
    Manages the transition between different scenes in the game.
    Each scene can handle its own input, update its state, and draw itself.
    """
    
    def __init__(self, initial_scene_name: str, screen: pygame.Surface) -> None:
        self.screen = screen
        self.scenes = {
            "MAIN_MENU": MainMenuScene(self),
            "GAME": GameScene(self),
        }
        if initial_scene_name not in self.scenes:
            raise ValueError(f"Initial scene '{initial_scene_name}' not found.")

        self.active_scene = self.scenes[initial_scene_name]
        self.clock = pygame.time.Clock()
        self.running = True

    def switch_scene(self, scene_name: str) -> None:
        if scene_name == "QUIT":
            self.running = False
        elif scene_name in self.scenes:
            self.active_scene = self.scenes[scene_name]
        else:
            print(f"Warning: Scene '{scene_name}' not found!")

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                self.active_scene.handle_input(event)

            self.active_scene.update(dt)
            self.screen.fill((0, 0, 0))
            self.active_scene.draw(self.screen)
            pygame.display.flip()
            
        pygame.quit()