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
        game_mode = game_settings.get('game_mode', "FFA") # Default to FFA

        # Common Y position for spawning players (they will fall to terrain)
        spawn_y = 150 

        player_spawn_positions: List[Tuple[int, int]] = []
        player_teams: List[PlayerTeam] = []

        if player_count == 4:
            print(f"Starting a 4-player game. Mode: {game_mode}")
            base_offset = self.terrain.width // 5
            player_spawn_positions = [
                (base_offset, spawn_y),            # Player 1
                (base_offset * 2, spawn_y),        # Player 2
                (base_offset * 3, spawn_y),        # Player 3
                (base_offset * 4, spawn_y)         # Player 4
            ]
            if game_mode == "TEAMS":
                print("Assigning teams for 4-player TEAMS mode.")
                # P1 & P3 (indices 0 & 2) vs P2 & P4 (indices 1 & 3)
                player_teams = [PlayerTeam.TEAM_1, PlayerTeam.TEAM_2, PlayerTeam.TEAM_1, PlayerTeam.TEAM_2]
            else: # FFA for 4 players
                print("Assigning teams for 4-player FFA mode (cosmetic).")
                player_teams = [PlayerTeam.TEAM_1, PlayerTeam.TEAM_2, PlayerTeam.TEAM_1, PlayerTeam.TEAM_2] # Or unique teams if desired for FFA colors
        elif player_count == 3:
            print("Starting a 3-player game (FFA).")
            player_spawn_positions = [
                (200, spawn_y),  # Player 1 (Left)
                (self.terrain.width // 2, spawn_y),  # Player 2 (Middle)
                (self.terrain.width - 200, spawn_y)  # Player 3 (Right)
            ]
            player_teams = [PlayerTeam.TEAM_1, PlayerTeam.TEAM_2, PlayerTeam.TEAM_1] # FFA cosmetic teams
        elif player_count == 2:
            print("Starting a 2-player game (FFA).")
            player_spawn_positions = [
                (200, spawn_y),
                (self.terrain.width - 200, spawn_y)
            ]
            player_teams = [PlayerTeam.TEAM_1, PlayerTeam.TEAM_2] # FFA cosmetic teams
        else: 
            print(f"Player count set to {player_count}. Defaulting to 2 players as specific logic is not met or count is unsupported (FFA).")
            player_spawn_positions = [
                (200, spawn_y),
                (self.terrain.width - 200, spawn_y)
            ]
            player_teams = [PlayerTeam.TEAM_1, PlayerTeam.TEAM_2]
            player_count = 2 # Ensure consistency if defaulted


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
            self.config['game_result'] = {'winner_team': None, 'winning_player_team': None}
            return False

        game_settings = self.config.get('game_settings', {})
        player_count_setting = game_settings.get('player_count', len(self.players))
        game_mode_setting = game_settings.get('game_mode', "FFA")

        is_team_mode_active = (player_count_setting == 4 and game_mode_setting == "TEAMS")

        if is_team_mode_active:
            team1_players = [p for p in self.players if p.team == PlayerTeam.TEAM_1]
            team2_players = [p for p in self.players if p.team == PlayerTeam.TEAM_2]

            # Ensure teams were actually formed (e.g. if player list is smaller than 4 but settings say 4 player teams)
            if not team1_players and not team2_players: # No players assigned to any team, or no players at all
                 self.winner_team = None
                 self.winning_player = None
                 print("Game Over! No players found in teams.")
                 self.config['game_result'] = {'winner_team': None, 'winning_player_team': None}
                 return True
            
            team1_alive = any(p.alive for p in team1_players) if team1_players else False
            team2_alive = any(p.alive for p in team2_players) if team2_players else False

            if team1_players and not team1_alive and team2_alive: # Team 1 eliminated, Team 2 wins
                self.winner_team = PlayerTeam.TEAM_2
                self.winning_player = None 
                print(f"Game Over! Team {self.winner_team.name} is the winner!")
                self.config['game_result'] = {'winner_team': self.winner_team.name, 'winning_player_team': None}
                return True
            elif team2_players and not team2_alive and team1_alive: # Team 2 eliminated, Team 1 wins
                self.winner_team = PlayerTeam.TEAM_1
                self.winning_player = None
                print(f"Game Over! Team {self.winner_team.name} is the winner!")
                self.config['game_result'] = {'winner_team': self.winner_team.name, 'winning_player_team': None}
                return True
            elif (team1_players and not team1_alive) and (team2_players and not team2_alive): # Both teams eliminated (draw)
                self.winner_team = None
                self.winning_player = None
                print("Game Over! It's a Draw between teams!")
                self.config['game_result'] = {'winner_team': None, 'winning_player_team': None}
                return True
            elif not team1_alive and not team2_alive and (not team1_players or not team2_players): # Edge case: one team might not have existed
                self.winner_team = None
                self.winning_player = None
                print("Game Over! Draw or invalid team setup.")
                self.config['game_result'] = {'winner_team': None, 'winning_player_team': None}
                return True


            # If game is not over yet for team mode
            self.winner_team = None
            self.winning_player = None
            self.config['game_result'] = {'winner_team': None, 'winning_player_team': None}
            return False
        else: # FFA logic (or any mode not 4-player TEAMS)
            alive_players = [p for p in self.players if p.alive]
            num_alive_players = len(alive_players)

            if len(self.players) == 0:
                self.winner_team = None
                self.winning_player = None
                self.config['game_result'] = {'winner_team': None, 'winning_player_team': None}
                return False
            
            # For 1 player mode (if ever formally supported beyond testing)
            if len(self.players) == 1:
                if num_alive_players == 0: # The single player died
                    self.winner_team = None 
                    self.winning_player = None
                    self.config['game_result'] = {'winner_team': None, 'winning_player_team': None}
                    return True
                self.winning_player = None # Game not over for the single player yet
                return False


            # Standard FFA: game is over if 1 or 0 players are left alive.
            if num_alive_players <= 1:
                if num_alive_players == 1:
                    self.winning_player = alive_players[0]
                    self.winner_team = self.winning_player.team # Store the team of the winning player
                    try:
                        winner_player_number = self.players.index(self.winning_player) + 1
                        print(f"Game Over! Player {winner_player_number} (Team {self.winner_team.name}) is the winner!")
                    except ValueError:
                        print(f"Game Over! Team {self.winner_team.name} is the winner (player index not found)!")
                else: # num_alive_players == 0
                    self.winner_team = None 
                    self.winning_player = None
                    print("Game Over! No players left alive (Draw).")
                self.config['game_result'] = {
                    'winner_team': self.winner_team.name if self.winner_team else None, 
                    'winning_player_team': self.winning_player.team.name if self.winning_player else None
                }
                return True
            
            self.winner_team = None 
            self.winning_player = None 
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
