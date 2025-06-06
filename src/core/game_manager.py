import pygame
import numpy as np # Keep for type hints if used elsewhere, or remove if only for simple_explosion_gradient
import math
from typing import Dict, Any, Tuple, List, Optional

from .terrain import Terrain, TerrainMap
from .player import Player, PlayerTeam
from .weapons.weapon import Weapon
from .weapons.basic_cannon import BasicCannon

# simple_explosion_gradient function is REMOVED from here.
# It's now a helper in projectile.py (or a shared utils module).

class GameManager:
    def __init__(self, config: dict) -> None:
        self.config = config
        self.terrain: Terrain = None
        self.players: List[Player] = []
        self.current_player_index: int = 0
        self.running: bool = False
        self.active_weapon: Optional[Weapon] = None

    def start_new_game(self, map: TerrainMap) -> None:
        self.terrain = Terrain(map, self.config)
        self.players = []
        # TODO: Get player count from config['game_settings']['player_count']
        # For now, defaulting to 2 players
        player1_start_pos = (200, 200) # These positions should be dynamic or from config
        player2_start_pos = (self.terrain.width - 200, 200)
        
        # Example: Use game_settings if available
        game_settings = self.config.get('game_settings', {})
        player_count = game_settings.get('player_count', 2) # Default to 2 if not set

        # For simplicity, still hardcoding 2 players for now, but showing where to use player_count
        # Actual player creation logic would need to adapt if player_count > 2

        # Player initialization - keeping as is from your current file for now
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
        print("Game started. Player 0's turn.")

    def next_turn(self):
        if not self.players or not self.running: return # Check self.running
        self.active_weapon = None
        
        # Find the next alive player
        original_index = self.current_player_index
        # Ensure players list is not empty before modulo
        if not self.players:
            self.running = False
            return
        while True:
            self.current_player_index = (self.current_player_index + 1) % len(self.players)
            if self.players[self.current_player_index].alive:
                print(f"Turn changed to Player {self.current_player_index}")
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

    def is_game_over(self) -> bool:
        if not self.players:
            return False # No players, game can't be over in a typical sense yet

        alive_players = [p for p in self.players if p.alive]
        num_alive_players = len(alive_players)

        if len(self.players) == 0 : # Should not happen if game started
            return False
        if len(self.players) == 1: # Single player mode (if ever implemented)
             return num_alive_players == 0

        # For 2+ players (current FFA setup): game is over if 1 or 0 players are left alive.
        if num_alive_players <= 1:
            if self.running: # Print only once
                if num_alive_players == 1:
                    print(f"Game Over! Player {alive_players[0].team.name} is the winner!")
                else:
                    print("Game Over! No players left alive.")
            return True
        return False

    def update(self, dt: float) -> Optional[str]: 
        if not self.running:
            return "GAME_OVER" # Return a status if game already ended

        if self.active_weapon:
            # Pass 'self' (GameManager instance) to the weapon's update method
            self.active_weapon.update(dt, self.terrain, self) 
            if self.active_weapon.is_finished():
                self.active_weapon = None
                # Check for game over AFTER the weapon's effects are resolved
                if self.is_game_over():
                    self.running = False 
                    return "GAME_OVER"
                self.next_turn()
        else:
            # Player movement/aiming is handled by GameScene based on input
            pass 

        # Fallback check, though primary check is after weapon action
        if self.is_game_over() and self.running: 
            self.running = False
            return "GAME_OVER"
            
        return None # Indicates game is ongoing

    # Removed the old 'explode' method.
    # def explode(self, x: int, y: int, owner=None) -> None:
    #     ...

    # New method to process impact data from weapons
    def process_impact_effect(self, impact_data: Dict[str, Any]):
        """
        Processes an impact effect reported by a weapon.
        'impact_data' now directly contains 'terrain_gradient' and 'terrain_gradient_offset'.
        Player damage is now calculated by the Player class using this gradient.
        """
        if not self.running: return

        print(f"GameManager processing impact: {impact_data}")
        
        # 1. Affect Terrain
        terrain_gradient_array = impact_data.get('terrain_gradient')
        terrain_gradient_offset = impact_data.get('terrain_gradient_offset') 
        
        if self.terrain and terrain_gradient_array is not None and terrain_gradient_offset is not None:
            if terrain_gradient_array.size > 0:
                self.terrain.destroy_terrain(terrain_gradient_offset, terrain_gradient_array)
                print(f"Terrain affected at offset {terrain_gradient_offset} with provided gradient.")
            else:
                print("Skipping terrain destruction due to empty gradient.")
        else:
            print("No pre-calculated terrain gradient or offset provided in impact_data for terrain.")

        # 2. Affect Players - New Logic
        # Players will use the same terrain_gradient_array and terrain_gradient_offset
        # The values in this gradient (derived from projectile's terrain_impact_strength)
        # will now directly translate to player damage.
        if terrain_gradient_array is not None and terrain_gradient_offset is not None and terrain_gradient_array.size > 0:
            for player in self.players:
                if player.alive:
                    player.process_explosion_damage(terrain_gradient_offset, terrain_gradient_array)
        elif impact_data.get('damage_values'): # Fallback for direct damage if specified (optional)
             damage_values = impact_data.get('damage_values')
             for player_instance, damage_amount in damage_values:
                if player_instance.alive and damage_amount > 0:
                    player_instance.apply_damage(damage_amount)
                    print(f"Player {player_instance.team.name} took direct damage {damage_amount}! HP: {player_instance.health}")
        else:
            print("No gradient data or direct damage values available to affect players.")

    # Renamed from prepare_shot
    def execute_player_action(self, weapon_type_id: str, angle: float, power: float):
        if self.active_weapon:
            print("Cannot execute action: An action is already in progress.")
            return

        active_player = self.get_active_player()
        if not active_player:
            print("Cannot execute action: No active player.")
            return

        # Future: Decrement weapon from player's inventory here
        # if active_player.has_weapon(weapon_type_id):
        #     active_player.consume_weapon(weapon_type_id) 
        # else:
        #     print(f"Player {active_player.team.name} does not have {weapon_type_id}. Cannot fire.")
        #     return

        print(f"Player {self.current_player_index} ({active_player.team.name}) executing action with {weapon_type_id}!")
        print(f"  Angle: {angle:.2f} degrees, Power: {power:.2f}")

        weapon_instance: Optional[Weapon] = None
        # Instantiate the selected weapon
        if weapon_type_id == "basic_cannon": # This ID should match what GameScene sends
            # Pass 'self' (GameManager) to the weapon if it needs to call back (e.g. process_impact_effect)
            weapon_instance = BasicCannon(owner=active_player, game_manager=self) 
        # elif weapon_type_id == "another_weapon_id":
        #     from .weapons.another_weapon import AnotherWeapon # Example
        #     weapon_instance = AnotherWeapon(owner=active_player, game_manager=self)
        else:
            print(f"Error: Unknown weapon type ID '{weapon_type_id}'. Cannot create weapon instance.")
            return 

        if weapon_instance:
            weapon_instance.activate(angle, power)
            self.active_weapon = weapon_instance # Mark that an action is in progress
        # No else needed here as the error is handled above

    def draw_components(self, screen: pygame.Surface) -> None:
        # Drawing can occur even if self.running is False (e.g. game over screen)
        if self.terrain: self.terrain.draw(screen)
        
        for player in self.players: 
            # Let Player.draw decide if it draws dead players or not, or add check here
            if player.alive:
                player.draw(screen) 
            
        if self.active_weapon: self.active_weapon.draw(screen)

        if not self.active_weapon and self.running: # Only draw indicator if game is running
            active_player = self.get_active_player()
            if active_player: # Active player is already checked for being alive by get_active_player
                indicator_pos = (int(active_player.x), int(active_player.y) - active_player.rect.height // 2 - 10)
                pygame.draw.circle(screen, (255, 255, 0), indicator_pos, 5)
