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
        self.winning_player: Optional[Player] = None # New attribute for the specific winning player
        self.current_turn_stage: TurnStage = TurnStage.MOVING # New attribute

    def start_new_game(self, map: TerrainMap) -> None:
        self.terrain = Terrain(map, self.config)
        self.players = []
        self.winner_team = None # Reset winner team
        self.winning_player = None # Reset winning player
        
        game_settings = self.config.get('game_settings', {})
        player_count = game_settings.get('player_count', 2) # Default to 2 if not set

        # Common Y position for spawning players (they will fall to terrain)
        spawn_y = 150 

        player_spawn_positions: List[Tuple[int, int]] = []
        player_teams: List[PlayerTeam] = []

        if player_count == 3:
            print("Starting a 3-player game.")
            player_spawn_positions = [
                (200, spawn_y),  # Player 1 (Left)
                (self.terrain.width // 2, spawn_y),  # Player 2 (Middle)
                (self.terrain.width - 200, spawn_y)  # Player 3 (Right)
            ]
            # In FFA, teams might just be for color/identification.
            # P1: Team 1, P2: Team 2, P3: Team 1 (could be Team 2 or a new Team 3 if defined)
            player_teams = [PlayerTeam.TEAM_1, PlayerTeam.TEAM_2, PlayerTeam.TEAM_1]
        elif player_count == 2:
            print("Starting a 2-player game.")
            player_spawn_positions = [
                (200, spawn_y),
                (self.terrain.width - 200, spawn_y)
            ]
            player_teams = [PlayerTeam.TEAM_1, PlayerTeam.TEAM_2]
        else: # Fallback for other counts (e.g., 4 if not yet implemented, or invalid values)
            print(f"Player count set to {player_count}. Defaulting to 2 players as 3-player specific logic is not met or count is unsupported.")
            player_spawn_positions = [
                (200, spawn_y),
                (self.terrain.width - 200, spawn_y)
            ]
            player_teams = [PlayerTeam.TEAM_1, PlayerTeam.TEAM_2]
            # Update player_count to actual number of players being created for consistency
            player_count = 2 


        for i in range(len(player_spawn_positions)):
            pos = player_spawn_positions[i]
            team = player_teams[i]
            player = Player(pos, team, self.config, self)
            self.players.append(player)

        self.current_player_index = 0
        self.active_weapon = None
        self.running = True
        self.current_turn_stage = TurnStage.MOVING # Reset stage
        if self.players:
            self.players[self.current_player_index].reset_turn_state()
        print(f"Game started with {len(self.players)} players. Player 0's turn. Stage: MOVING")

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

    def get_winning_player(self) -> Optional[Player]:
        """Returns the specific player object that won, if any."""
        return self.winning_player

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
            self.winning_player = None
            self.config['game_result'] = {'winner_team': None} # Store result
            return False # No players, game can't be over in a typical sense yet

        alive_players = [p for p in self.players if p.alive]
        num_alive_players = len(alive_players)

        if len(self.players) == 0 : # Should not happen if game started
            self.winner_team = None
            self.winning_player = None
            self.config['game_result'] = {'winner_team': None} # Store result
            return False
        if len(self.players) == 1: # Single player mode (if ever implemented)
            if num_alive_players == 0:
                self.winner_team = None # Or potentially a "draw" or "loss" state
                self.winning_player = None
                self.config['game_result'] = {'winner_team': None} # Store result
                return True
            # If single player is alive, game is not over yet for them.
            self.winning_player = None # Ensure it's clear no one has "won" yet in terms of game over
            return False


        # For 2+ players (current FFA setup): game is over if 1 or 0 players are left alive.
        if num_alive_players <= 1:
            if num_alive_players == 1:
                self.winning_player = alive_players[0]
                self.winner_team = self.winning_player.team
                # Determine player number for the print message
                try:
                    winner_player_number = self.players.index(self.winning_player) + 1
                    print(f"Game Over! Player {winner_player_number} (Team {self.winner_team.name}) is the winner!")
                except ValueError: # Should not happen
                    print(f"Game Over! Team {self.winner_team.name} is the winner (player index not found)!")
            else:
                self.winner_team = None # No winner if all die simultaneously
                self.winning_player = None
                print("Game Over! No players left alive.")
            self.config['game_result'] = {'winner_team': self.winner_team, 'winning_player_team': self.winning_player.team.name if self.winning_player else None} # Store result
            return True
        
        self.winner_team = None # Game not over, no winner yet
        self.winning_player = None # Game not over, no winning player yet
        self.config['game_result'] = {'winner_team': None, 'winning_player_team': None} 
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
