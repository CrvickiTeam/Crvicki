import pygame
import numpy as np
import math
from typing import Dict, Any, Tuple, List, Optional

from .terrain import Terrain, TerrainMap
from .player import Player, PlayerTeam
from .weapons.weapon import Weapon
from .weapons.basic_cannon import BasicCannon
from enum import Enum, auto

class TurnStage(Enum):
    MOVING = auto()
    AIMING = auto()

def simple_explosion_gradient(x: int, y: int, radius: int, center_strength: int) -> Tuple[int, int, np.ndarray]:
    gradient = np.zeros((radius * 2 + 1, radius * 2 + 1), dtype=np.uint8)
    center_x, center_y = radius, radius
    for i in range(gradient.shape[0]):
        for j in range(gradient.shape[1]):
            dx = i - center_x; dy = j - center_y
            distance = (dx ** 2 + dy ** 2) ** 0.5
            if distance <= radius:
                strength = int(center_strength * (1 - distance / radius))
                gradient[i, j] = strength
    start_x = x - radius; start_y = y - radius
    return start_x, start_y, gradient


class GameManager:
    def __init__(self, config: dict) -> None:
        self.config = config
        self.terrain: Terrain = None
        self.players: List[Player] = []
        self.current_player_index: int = 0
        self.running: bool = False
        self.active_weapon: Optional[Weapon] = None
        self.winner_team: Optional[PlayerTeam] = None
        self.current_turn_stage: TurnStage = TurnStage.MOVING # New attribute

    def start_new_game(self, map: TerrainMap) -> None:
        self.terrain = Terrain(map, self.config)
        self.players = []
        self.winner_team = None # Reset winner
        # TODO: Get player count from config['game_settings']['player_count']
        # For now, defaulting to 2 players
        player1_start_pos = (200, 200) # These positions should be dynamic or from config
        player2_start_pos = (self.terrain.width - 200, 200)
        
        # Example: Use game_settings if available
        game_settings = self.config.get('game_settings', {})
        player_count = game_settings.get('player_count', 2) # Default to 2 if not set

        # For simplicity, still hardcoding 2 players for now, but showing where to use player_count
        # Actual player creation logic would need to adapt if player_count > 2

        player1 = Player(player1_start_pos, PlayerTeam.TEAM_1, self.config, self)
        player2 = Player(player2_start_pos, PlayerTeam.TEAM_2, self.config, self)
        self.players.append(player1)
        self.players.append(player2)

        # Add more players based on player_count if logic is expanded
        # if player_count >= 3:
        #     player3_start_pos = (self.terrain.width // 2, 150)
        #     player3 = Player(player3_start_pos, PlayerTeam.TEAM_1, self.config) # Or new team
        #     self.players.append(player3)
        # if player_count >= 4:
        #     player4_start_pos = (self.terrain.width // 2 + 100, 150)
        #     player4 = Player(player4_start_pos, PlayerTeam.TEAM_2, self.config) # Or new team
        #     self.players.append(player4)


        self.current_player_index = 0
        self.active_weapon = None
        self.running = True
        self.current_turn_stage = TurnStage.MOVING # Reset stage
        if self.players:
            self.players[self.current_player_index].reset_turn_state()
        print("Game started. Player 0's turn. Stage: MOVING")

    def next_turn(self):
        if not self.players or not self.running: return # Check self.running
        self.active_weapon = None
        self.current_turn_stage = TurnStage.MOVING # Reset to moving stage
        
        # Find the next alive player
        original_index = self.current_player_index
        while True:
            self.current_player_index = (self.current_player_index + 1) % len(self.players)
            active_player = self.players[self.current_player_index]
            if active_player.alive:
                active_player.reset_turn_state() # Reset distance moved for the new player
                print(f"Turn changed to Player {self.current_player_index}. Stage: MOVING")
                break
            if self.current_player_index == original_index: # Cycled through all players, none are alive (should be caught by is_game_over)
                print("No alive players left to switch turn to.")
                self.running = False # Should be caught by game over logic earlier
                break

    def get_active_player(self) -> Player | None:
        if self.running and self.players and 0 <= self.current_player_index < len(self.players):
            if self.players[self.current_player_index].alive:
                return self.players[self.current_player_index]
        return None

    def get_winner_team(self) -> Optional[PlayerTeam]:
        return self.winner_team

    def switch_to_aiming_stage(self):
        if self.current_turn_stage == TurnStage.MOVING:
            self.current_turn_stage = TurnStage.AIMING
            active_player = self.get_active_player()
            if active_player:
                active_player.stop_moving() # Ensure player stops moving when switching to aiming
            print(f"Player {self.current_player_index} switched to AIMING stage.")

    def is_game_over(self) -> bool:
        if not self.players:
            self.winner_team = None
            self.config['game_result'] = {'winner_team': None} # Store result
            return False # No players, game can't be over in a typical sense yet

        alive_players = [p for p in self.players if p.alive]
        num_alive_players = len(alive_players)

        if len(self.players) == 0 : # Should not happen if game started
            self.winner_team = None
            self.config['game_result'] = {'winner_team': None} # Store result
            return False
        if len(self.players) == 1: # Single player mode (if ever implemented)
            if num_alive_players == 0:
                self.winner_team = None # Or potentially a "draw" or "loss" state
                self.config['game_result'] = {'winner_team': None} # Store result
                return True
            # If single player is alive, game is not over yet for them.
            return False


        # For 2+ players (current FFA setup): game is over if 1 or 0 players are left alive.
        if num_alive_players <= 1:
            if num_alive_players == 1:
                self.winner_team = alive_players[0].team
                print(f"Game Over! Player {self.winner_team.name} is the winner!")
            else:
                self.winner_team = None # No winner if all die simultaneously
                print("Game Over! No players left alive.")
                self.config['game_result'] = {'winner_team': self.winner_team} # Store result
            return True
        self.winner_team = None
        self.config['game_result'] = {'winner_team': None} # Game not over, no winner yet
        return False

    def update(self, dt: float) -> Optional[str]: 
        if not self.running:
            return None # Or "GAME_ALREADY_ENDED" if specific status needed

        # Check for automatic stage transition if player moved max distance
        active_player = self.get_active_player()
        if active_player and self.current_turn_stage == TurnStage.MOVING:
            if active_player.distance_moved_this_turn >= active_player.max_move_distance_per_turn:
                self.switch_to_aiming_stage()

        if self.active_weapon:
            self.active_weapon.update(dt, self.terrain)
            if self.active_weapon.is_finished():
                self.active_weapon = None
                if self.is_game_over():
                    self.running = False # Stop game logic
                    return "GAME_OVER"
                self.next_turn()
        else:
            # Player movement updates (less likely to cause game over directly)
            # This part of update is mostly for player input handling before a shot
            # The primary game over check is after a weapon action.
            pass # Player movement is handled by GameScene based on input

        # Fallback check, though primary check is after weapon action
        if self.is_game_over() and self.running: # Check self.running to avoid double "GAME_OVER"
            self.running = False
            return "GAME_OVER"
            
        return None

    def explode(self, x: int, y: int, owner=None) -> None:
        if not self.terrain: return
        radius = 25 # Explosion radius from config or weapon
        strength = 100 # Explosion strength from config or weapon
        origin_x, origin_y, gradient = simple_explosion_gradient(x, y, radius, strength)
        self.terrain.destroy_terrain((origin_x, origin_y), gradient)
        explosion_pos = (x, y)
        max_damage = 50  # Max damage at center, from config or weapon

        for player in self.players:
            if not player.alive: # Don't process already dead players
                continue
            # if player == owner: # Typically, owner is not immune unless specified by weapon
            #     continue
            dx = player.x - explosion_pos[0]
            dy = player.y - explosion_pos[1]
            distance = math.hypot(dx, dy)

            if distance < radius:
                damage = int(max_damage * (1 - distance / radius))
                player.apply_damage(damage) # apply_damage sets player.alive to False if HP <= 0
                print(f"Player {player.team.name} took {damage} damage! Remaining HP: {player.health}")
        
        # No immediate game over check here, it will be caught by the main update loop
        # when the weapon action finishes. This keeps explode focused on damage.

    def prepare_shot(self, angle: float, power: float):
        if self.active_weapon:
            print("Cannot fire: Weapon effect already in progress.")
            return

        if self.current_turn_stage != TurnStage.AIMING:
            print("Cannot fire: Not in aiming stage.")
            return

        active_player = self.get_active_player()
        if not active_player:
            print("Cannot fire: No active player.")
            return

        print(f"Player {self.current_player_index} firing!")
        print(f"  Angle: {angle:.2f} degrees")
        print(f"  Power: {power:.2f}")


        weapon_instance = BasicCannon(active_player, self)
        weapon_instance.activate(angle, power)
        self.active_weapon = weapon_instance


    def draw_components(self, screen: pygame.Surface) -> None:
        if not self.running: return
        if self.terrain: self.terrain.draw(screen)
        for player in self.players: player.draw(screen)
        if self.active_weapon: self.active_weapon.draw(screen)

        if not self.active_weapon:
            active_player = self.get_active_player()
            if active_player:
                indicator_pos = (int(active_player.x), int(active_player.y) - active_player.rect.height // 2 - 10)
                pygame.draw.circle(screen, (255, 255, 0), indicator_pos, 5)
