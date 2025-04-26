from .terrain import Terrain

class GameState:

    def __init__(self, config: dict) -> None:
        """
        Initializes the game state with the given configuration.

        Args:
            config: The main configuration dictionary.
        """
        self.config = config
        self.terrain = Terrain(config)
        self._setup_initial_state()

    def _setup_initial_state(self) -> None:
        """
        Sets up the initial state of the game. This includes initializing the terrain and any other game elements.
        """
        # Initialize other game elements here if needed
        pass

    def update(self, dt: float) -> None:
        """
        Updates the game state. This method should be called every frame to update the game logic.

        Args:
            dt: The time since the last frame in seconds.
        """
        # Update game elements here
        pass