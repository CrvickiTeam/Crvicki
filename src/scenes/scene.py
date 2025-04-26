from __future__ import annotations
from typing import Dict, Any, TYPE_CHECKING
if TYPE_CHECKING:
    from core.scene_manager import SceneManager
    from pygame.surface import Surface
    from pygame.event import Event

class Scene:
    """Base class for all scenes in the game."""

    def __init__(self, manager: SceneManager, config: Dict[str, Any]) -> None:
        self.manager = manager
        self.config = config
        self.screen_width: int = config.get("display", {}).get("width", 800)
        self.screen_height: int = config.get("display", {}).get("height", 600)

    def handle_input(self, event: Event) -> None:
        """Process events (keyboard, mouse, etc.)."""
        pass

    def update(self, dt: float) -> None:
        """Update scene state (logic, animations)."""
        pass

    def draw(self, screen: Surface) -> None:
        """Draw the scene to the screen."""
        pass