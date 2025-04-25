class Scene:
    """Base class for all scenes in the game."""
    
    def __init__(self, manager):
        self.manager = manager

    def handle_input(self, event):
        """Process events (keyboard, mouse, etc.)."""
        pass

    def update(self, dt):
        """Update scene state (logic, animations)."""
        pass

    def draw(self, screen):
        """Draw the scene to the screen."""
        pass