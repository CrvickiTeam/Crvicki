import pygame
import numpy as np # Ensure numpy is imported
from typing import Dict, Any, Tuple, List, Optional

from .terrain import Terrain, TerrainMap # Assuming TerrainMap might be used elsewhere
from .player import Player, PlayerTeam 
from .weapons.weapon import Weapon
# from .weapons.basic_cannon import BasicCannon
from .weapons.small_bomb import SmallBomb # Add this
# from .weapons.sniper_rifle import SniperRifle # Future weapon
# from .weapons.big_bomb_cannon import BigBombCannon # Future weapon
# from .weapons.cluster_gun import ClusterGun # Future weapon


class GameManager:
    def __init__(self, config: Dict[str, Any]) -> None: # Type hint for config
        self.config: Dict[str, Any] = config
        self.terrain: Optional[Terrain] = None # Terrain can be None initially
        self.players: List[Player] = []
        self.current_player_index: int = 0
        self.running: bool = False
        self.active_weapon: Optional[Weapon] = None
        self.winner_team: Optional[PlayerTeam] = None
        self.winning_player: Optional[Player] = None 
        # self.current_turn_stage: TurnStage = TurnStage.MOVING # REMOVE THIS ATTRIBUTE

    def start_new_game(self, map_type: TerrainMap) -> None: # Renamed map to map_type for clarity
        self.terrain = Terrain(map_type, self.config)
        self.players = []
        self.winner_team = None 
        self.winning_player = None 
        
        game_settings: Dict[str, Any] = self.config.get('game_settings', {})
        player_count: int = game_settings.get('player_count', 2)
        game_mode: str = game_settings.get('game_mode', "FFA")

        spawn_y: int = 150 

        player_spawn_positions: List[Tuple[int, int]] = []
        player_teams: List[PlayerTeam] = []

        # Player spawning logic (current code seems fine, ensure terrain width is available)
        if self.terrain:
            terrain_width = self.terrain.width
            if player_count == 4:
                base_offset = terrain_width // 5
                player_spawn_positions = [
                    (base_offset, spawn_y), (base_offset * 2, spawn_y),
                    (base_offset * 3, spawn_y), (base_offset * 4, spawn_y)
                ]
                player_teams = [PlayerTeam.TEAM_1, PlayerTeam.TEAM_2, PlayerTeam.TEAM_1, PlayerTeam.TEAM_2] if game_mode == "TEAMS" else [PlayerTeam.TEAM_1, PlayerTeam.TEAM_2, PlayerTeam.TEAM_1, PlayerTeam.TEAM_2]
            elif player_count == 3:
                player_spawn_positions = [
                    (200, spawn_y), (terrain_width // 2, spawn_y), (terrain_width - 200, spawn_y)
                ]
                player_teams = [PlayerTeam.TEAM_1, PlayerTeam.TEAM_2, PlayerTeam.TEAM_1]
            elif player_count == 2:
                player_spawn_positions = [
                    (200, spawn_y), (terrain_width - 200, spawn_y)
                ]
                player_teams = [PlayerTeam.TEAM_1, PlayerTeam.TEAM_2]
            else: 
                player_spawn_positions = [
                    (200, spawn_y), (terrain_width - 200, spawn_y)
                ]
                player_teams = [PlayerTeam.TEAM_1, PlayerTeam.TEAM_2]
                player_count = 2
        else: # Fallback if terrain is not initialized (should not happen in normal flow)
            print("Error: Terrain not initialized in start_new_game.")
            return


        for i in range(len(player_spawn_positions)):
            pos = player_spawn_positions[i]
            team = player_teams[i]
            # Assuming Player class constructor signature is (start_pos, team, config, game_manager)
            player = Player(pos, team, self.config, self) 
            self.players.append(player)

        self.current_player_index = 0
        self.active_weapon = None
        self.running = True
        # self.current_turn_stage = TurnStage.MOVING # REMOVE THIS
        if self.players: # Ensure players list is not empty
            current_player = self.players[self.current_player_index]
            if hasattr(current_player, 'reset_turn_state'): # Check if method exists
                current_player.reset_turn_state() # Player resets its own state (e.g., movement fuel)
        print(f"Game started with {len(self.players)} players. Player 0's turn.")

    def next_turn(self) -> None:
        if not self.players or not self.running: return
        self.active_weapon = None
        # self.current_turn_stage = TurnStage.MOVING # REMOVE THIS
        
        original_index: int = self.current_player_index
        if not self.players:
            self.running = False
            return

        num_players: int = len(self.players)
        for _ in range(num_players): # Iterate at most num_players times to find next alive player
            self.current_player_index = (self.current_player_index + 1) % num_players
            active_player = self.players[self.current_player_index]
            if active_player.alive:
                if hasattr(active_player, 'reset_turn_state'): # Check if method exists
                    active_player.reset_turn_state() 
                print(f"Turn changed to Player {self.current_player_index}.")
                return # Found next player
            # if self.current_player_index == original_index: # This check is implicitly handled by the loop limit
            #     break 
        
        # If loop finishes, it means no alive players were found (or only one was left and it's their turn again)
        # Game over logic should handle this, but as a fallback:
        print("No other alive players left to switch turn to, or game should be over.")
        # self.running = False # Game over logic in update/is_game_over should handle this

    def get_active_player(self) -> Optional[Player]:
        if self.running and self.players and 0 <= self.current_player_index < len(self.players):
            player = self.players[self.current_player_index]
            if player.alive:
                return player
        return None

    def get_winner_team(self) -> Optional[PlayerTeam]:
        return self.winner_team

    def get_winning_player(self) -> Optional[Player]:
        return self.winning_player

    # def switch_to_aiming_stage(self) -> None: # REMOVE THIS METHOD
    #     if self.current_turn_stage == TurnStage.MOVING:
    #         self.current_turn_stage = TurnStage.AIMING
    #         active_player = self.get_active_player()
    #         if active_player:
    #             active_player.stop_moving() 
    #         print(f"Player {self.current_player_index} switched to AIMING stage.")

    def is_game_over(self) -> bool:
        # ... (current is_game_over logic seems mostly fine, ensure it correctly sets self.winner_team and self.winning_player) ...
        # Minor refinement: ensure config['game_result'] is always set before returning True
        if not self.players:
            self.winner_team = None
            self.winning_player = None
            self.config['game_result'] = {'winner_team': None, 'winning_player_team': None, 'reason': 'No players'}
            return True # Game cannot continue without players

        game_settings: Dict[str, Any] = self.config.get('game_settings', {})
        player_count_setting: int = game_settings.get('player_count', len(self.players))
        game_mode_setting: str = game_settings.get('game_mode', "FFA")
        is_team_mode_active: bool = (player_count_setting == 4 and game_mode_setting == "TEAMS")

        reason_for_game_over = "Game ended" # Default reason

        if is_team_mode_active:
            team1_players: List[Player] = [p for p in self.players if p.team == PlayerTeam.TEAM_1]
            team2_players: List[Player] = [p for p in self.players if p.team == PlayerTeam.TEAM_2]

            if not team1_players and not team2_players:
                 self.winner_team = None; self.winning_player = None; reason_for_game_over = "No players in teams"
                 self.config['game_result'] = {'winner_team': None, 'winning_player_team': None, 'reason': reason_for_game_over}
                 return True
            
            team1_alive: bool = any(p.alive for p in team1_players) if team1_players else False
            team2_alive: bool = any(p.alive for p in team2_players) if team2_players else False

            if team1_players and not team1_alive and team2_alive:
                self.winner_team = PlayerTeam.TEAM_2; self.winning_player = None; reason_for_game_over = f"Team {PlayerTeam.TEAM_2.name} wins"
            elif team2_players and not team2_alive and team1_alive:
                self.winner_team = PlayerTeam.TEAM_1; self.winning_player = None; reason_for_game_over = f"Team {PlayerTeam.TEAM_1.name} wins"
            elif (team1_players and not team1_alive) and (team2_players and not team2_alive):
                self.winner_team = None; self.winning_player = None; reason_for_game_over = "Draw between teams"
            elif not team1_alive and not team2_alive: # Covers cases where one or both teams might not have existed but all are dead
                self.winner_team = None; self.winning_player = None; reason_for_game_over = "Draw or invalid team setup"
            else: # Game not over for team mode
                self.config['game_result'] = {'winner_team': None, 'winning_player_team': None, 'reason': 'Ongoing'}
                return False
            
            print(f"Game Over! {reason_for_game_over}")
            self.config['game_result'] = {'winner_team': self.winner_team.name if self.winner_team else None, 'winning_player_team': None, 'reason': reason_for_game_over}
            return True
        else: # FFA logic
            alive_players: List[Player] = [p for p in self.players if p.alive]
            num_alive_players: int = len(alive_players)

            if len(self.players) <= 1 and num_alive_players == 0 : # e.g. single player game and player died, or 0 players started
                self.winner_team = None; self.winning_player = None; reason_for_game_over = "No players left or single player died"
            elif num_alive_players == 1 and len(self.players) > 0 : # Only one player left alive in FFA
                self.winning_player = alive_players[0]
                self.winner_team = self.winning_player.team
                reason_for_game_over = f"Player (Team {self.winner_team.name}) wins"
            elif num_alive_players == 0 and len(self.players) > 0: # All players died in FFA
                self.winner_team = None; self.winning_player = None; reason_for_game_over = "Draw, no players left alive"
            else: # Game not over for FFA (more than 1 player alive)
                self.config['game_result'] = {'winner_team': None, 'winning_player_team': None, 'reason': 'Ongoing'}
                return False

            print(f"Game Over! {reason_for_game_over}")
            self.config['game_result'] = {
                'winner_team': self.winner_team.name if self.winner_team else None, 
                'winning_player_team': self.winning_player.team.name if self.winning_player else None,
                'reason': reason_for_game_over
            }
            return True

    def update(self, dt: float) -> Optional[str]: 
        if not self.running:
            return "GAME_ALREADY_ENDED" 

        # active_player = self.get_active_player() # REMOVE STAGE SWITCHING LOGIC
        # if active_player and self.current_turn_stage == TurnStage.MOVING:
        #     # Assuming Player has these attributes, set from config and updated during Player.move_left/right
        #     if hasattr(active_player, 'distance_moved_this_turn') and \
        #        hasattr(active_player, 'max_move_distance_per_turn'):
        #         if active_player.distance_moved_this_turn >= active_player.max_move_distance_per_turn:
        #             self.switch_to_aiming_stage() # This method is removed

        if self.active_weapon:
            if self.terrain: # Ensure terrain is available for weapon update
                self.active_weapon.update(dt, self.terrain, self) 
            if self.active_weapon.is_finished():
                self.active_weapon = None
                if self.is_game_over(): # Check game over immediately after weapon effects
                    self.running = False 
                    return "GAME_OVER"
                self.next_turn()
        
        # Check game over again, in case conditions changed without a weapon firing (e.g., player falling out of map)
        if self.running and self.is_game_over(): 
            self.running = False
            return "GAME_OVER"
            
        return None 

    def process_impact_effect(self, impact_data: Dict[str, Any]) -> None:
        if not self.running or not impact_data:
            return
        
        effect_gradient_array: Optional[np.ndarray] = impact_data.get('effect_gradient')
        gradient_origin_offset: Optional[Tuple[int, int]] = impact_data.get('gradient_origin') 
        
        # --- Terrain Destruction ---
        if self.terrain and effect_gradient_array is not None and gradient_origin_offset is not None:
            if effect_gradient_array.size > 0:
                # Assuming Terrain class has a method like destroy_terrain or apply_gradient
                # Based on your player.py, terrain likely has a similar method or direct grid manipulation
                self.terrain.destroy_terrain(gradient_origin_offset, effect_gradient_array)
        
        # --- Player Damage ---
        # Player.process_explosion_damage will be called for each player
        if effect_gradient_array is not None and gradient_origin_offset is not None and effect_gradient_array.size > 0:
            owner_player: Optional[Player] = impact_data.get('owner')
            for player in self.players:
                if player.alive: # Ensure player is alive before processing damage
                    # Player class has process_explosion_damage which internally calls apply_damage
                    player.process_explosion_damage(gradient_origin_offset, effect_gradient_array)
        
        # This section for 'damage_values' was an alternative system.
        # Based on your player.py, the process_explosion_damage method is the primary way players take damage from explosions.
        # If 'damage_values' is a separate mechanic (e.g., direct damage not from a gradient),
        # it should be handled distinctly.
        # For now, assuming explosion damage is handled by player.process_explosion_damage.
        # The 'elif' for 'damage_values' is removed to avoid confusion if it's not currently used
        # or if its intent was covered by the gradient system.
        # If 'damage_values' represents a different type of damage (e.g. poison, direct non-explosive hit),
        # then it would need its own clear logic.
        # Given the context of explosions, the gradient processing is the primary path.

    def execute_player_action(self, weapon_type_id: str, angle: float, power: float) -> None:
        if self.active_weapon:
            # print("Cannot fire: Weapon effect already in progress.") # Optional: keep for debugging
            return

        active_player = self.get_active_player()
        if not active_player:
            # print("Cannot execute action: No active player.") # Optional: keep for debugging
            return

        # print(f"Player {self.current_player_index} ({active_player.team.name}) executing action with {weapon_type_id}!")
        # print(f"  Angle: {angle:.2f} degrees, Power: {power:.2f}")

        weapon_instance: Optional[Weapon] = None
        # if weapon_type_id == "basic_cannon":  # Old
        #     weapon_instance = BasicCannon(owner=active_player, game_manager=self) 
        if weapon_type_id == "small_bomb": # New - ensure this matches the string used in GameScene
            weapon_instance = SmallBomb(owner=active_player, game_manager=self)
        # Add other weapon types here later:
        # elif weapon_type_id == "sniper_rifle":
        #     weapon_instance = SniperRifle(owner=active_player, game_manager=self)
        # elif weapon_type_id == "big_bomb_cannon":
        #     weapon_instance = BigBombCannon(owner=active_player, game_manager=self)
        # elif weapon_type_id == "cluster_gun":
        #     weapon_instance = ClusterGun(owner=active_player, game_manager=self)
        else:
            print(f"Error: Unknown weapon type ID '{weapon_type_id}'. Cannot create weapon instance.")
            return 

        if weapon_instance:
            weapon_instance.activate(angle, power)
            self.active_weapon = weapon_instance
    
    def draw_components(self, screen: pygame.Surface) -> None:
        if self.terrain: self.terrain.draw(screen)
        
        for player in self.players: 
            # Player.draw should handle whether to draw if not alive, or add check here
            player.draw(screen) # Let player.draw handle its alive state for drawing
            
        if self.active_weapon: self.active_weapon.draw(screen)

        # Draw active player indicator only if game is running and no weapon is active
        if self.running and not self.active_weapon: 
            active_player = self.get_active_player()
            if active_player: 
                indicator_pos = (int(active_player.x), int(active_player.y) - active_player.rect.height // 2 - 10)
                pygame.draw.circle(screen, (255, 255, 0), indicator_pos, 5)
