import pygame
import sys
import random
from enum import Enum
from collections import defaultdict, deque
from heapq import heappush, heappop
import math

from constants import *

class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.health = 100
        self.max_health = 100
        self.level = 1
        self.experience = 0
        
    def move(self, dx, dy, dungeon_map, enemies=None):
        new_x = self.x + dx
        new_y = self.y + dy
        
        # Check bounds
        if (new_x < 0 or new_x >= len(dungeon_map[0]) or 
            new_y < 0 or new_y >= len(dungeon_map)):
            return False
        
        # Check wall collision
        if dungeon_map[new_y][new_x] == CellType.WALL:
            return False
        
        # Check enemy collision
        if enemies:
            for enemy in enemies:
                if enemy.alive and enemy.x == new_x and enemy.y == new_y:
                    return False
        
        # Move if path is clear
        self.x = new_x
        self.y = new_y
        return True
    
    def take_damage(self, damage):
        self.health = max(0, self.health - damage)
        return self.health <= 0
        
    def heal(self, amount):
        self.health = min(self.max_health, self.health + amount)
        
    def gain_experience(self, exp):
        self.experience += exp
        if self.experience >= self.level * 100:
            self.level_up()
    
    def level_up(self):
        self.level += 1
        self.max_health += 15
        self.health = self.max_health
        self.experience = 0

class Enemy:
    def __init__(self, x, y, enemy_type="goblin", level=1):
        self.x = x
        self.y = y
        self.type = enemy_type
        self.level = level
        self.alive = True
        self.move_timer = 0
        self.attack_timer = 0
        self.projectile_timer = 0
        
        # Set properties based on enemy type
        self.setup_enemy_stats()

    def setup_enemy_stats(self):
        # Meele
        if self.type == "goblin":
            self.health = 20 + random.randint(0, 10)
            self.max_health = self.health
            self.damage = 15 + random.randint(0, 5)
            self.is_ranged = False
            self.attack_range = 1
            self.color = ENEMY_GOBLIN
        
        # Meele
        elif self.type == "orc":
            self.health = 40 + random.randint(0, 20)
            self.max_health = self.health
            self.damage = 25 + random.randint(0, 10)
            self.is_ranged = False
            self.attack_range = 1
            self.color = ENEMY_ORC
        
        # Ranged
        elif self.type == "archer":
            self.health = 20
            self.max_health = self.health
            self.damage = 20 + random.randint(0, 10)
            self.is_ranged = True
            self.attack_range = 6
            self.color = ENEMY_ARCHER
        
        # Ranged    
        elif self.type == "mage":
            self.health = 40
            self.max_health = self.health
            self.damage = 30 + random.randint(0, 15)
            self.is_ranged = True
            self.attack_range = 8
            self.color = ENEMY_MAGE
        
        # Ranged    
        elif self.type == "boss":
            self.health = 100
            self.max_health = self.health
            self.damage = 40 + random.randint(0, 20)
            self.is_ranged = True
            self.attack_range = 10
            self.color = ENEMY_BOSS

    def take_damage(self, damage): # Taking damage from player
        self.health -= damage
        if self.health <= 0:
            self.alive = False
            return True
        return False

    def find_path_to_player(self, player_x, player_y, dungeon_map): # Use A* to find player position
        from heapq import heappush, heappop
        
        start = (self.x, self.y)
        goal = (player_x, player_y)
        
        if start == goal:
            return []
        
        # A* algorithm
        open_set = []
        heappush(open_set, (0, start))
        came_from = {}
        g_score = {start: 0}
        f_score = {start: self.heuristic(start, goal)}
        
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]  # Down, Up, Right, Left
        
        while open_set:
            current = heappop(open_set)[1]
            
            if current == goal:
                # Reconstruct path
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                return path[::-1]  # Reverse to get path from start to goal
            
            for dx, dy in directions:
                neighbor = (current[0] + dx, current[1] + dy)
                nx, ny = neighbor
                
                # Check bounds and walls
                if (0 <= nx < len(dungeon_map[0]) and 
                    0 <= ny < len(dungeon_map) and 
                    dungeon_map[ny][nx] != CellType.WALL):
                    
                    tentative_g_score = g_score[current] + 1
                    
                    if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                        came_from[neighbor] = current
                        g_score[neighbor] = tentative_g_score
                        f_score[neighbor] = tentative_g_score + self.heuristic(neighbor, goal)
                        heappush(open_set, (f_score[neighbor], neighbor))
        
        return []  # No path found

    def heuristic(self, a, b): # Manhattan Heuristic Distance
        return abs(a[0] - b[0]) + abs(a[1] - b[1])
        
    def move_towards_player(self, player_x, player_y, dungeon_map, other_enemies):
        if self.move_timer > 0:
            self.move_timer -= 1
            return
            
        self.move_timer = 30  # Move every 30 frames
        
        # Calculate distance to player
        distance_to_player = abs(self.x - player_x) + abs(self.y - player_y)
        
        # Only chase player if within detection range
        if distance_to_player <= ENEMY_DETECTION_RANGE:
            # Find path to player using A*
            path = self.find_path_to_player(player_x, player_y, dungeon_map)
            
            if not path:
                # If no path found, try random movement to get unstuck
                self.random_movement(dungeon_map, other_enemies)
                return
            
            # Move to next position in path
            next_pos = path[0] if path else None
            if next_pos:
                new_x, new_y = next_pos
                
                # Check collision with player (don't move into player)
                if new_x == player_x and new_y == player_y:
                    return
                
                # Check collision with other enemies
                collision = False
                for other_enemy in other_enemies:
                    if (other_enemy != self and other_enemy.alive and 
                        other_enemy.x == new_x and other_enemy.y == new_y):
                        collision = True
                        break
                
                # Move if no collision, otherwise try alternative movement
                if not collision:
                    self.x, self.y = new_x, new_y
                else:
                    # Try to find alternative path or wait
                    self.handle_collision_movement(player_x, player_y, dungeon_map, other_enemies)
        else:
            # Player is too far, do patrol behavior instead
            self.patrol_behavior(dungeon_map, other_enemies)

    def random_movement(self, dungeon_map, other_enemies):
        # Helping if they stuck
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        random.shuffle(directions)
        
        for dx, dy in directions:
            new_x = self.x + dx
            new_y = self.y + dy
            
            # Check bounds and walls
            if (0 <= new_x < len(dungeon_map[0]) and 
                0 <= new_y < len(dungeon_map) and 
                dungeon_map[new_y][new_x] != CellType.WALL):
                
                # Check collision with other enemies
                collision = False
                for other_enemy in other_enemies:
                    if (other_enemy != self and other_enemy.alive and 
                        other_enemy.x == new_x and other_enemy.y == new_y):
                        collision = True
                        break
                
                if not collision:
                    self.x, self.y = new_x, new_y
                    break

    def handle_collision_movement(self, player_x, player_y, dungeon_map, other_enemies): # Handle movement if there's collision with enemies
        # Try to move around the obstacle
        current_distance = abs(self.x - player_x) + abs(self.y - player_y)
        
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        best_move = None
        best_distance = float('inf')
        
        for dx, dy in directions:
            new_x = self.x + dx
            new_y = self.y + dy
            
            # Check bounds and walls
            if (0 <= new_x < len(dungeon_map[0]) and 
                0 <= new_y < len(dungeon_map) and 
                dungeon_map[new_y][new_x] != CellType.WALL):
                
                # Check collision with other enemies
                collision = False
                for other_enemy in other_enemies:
                    if (other_enemy != self and other_enemy.alive and 
                        other_enemy.x == new_x and other_enemy.y == new_y):
                        collision = True
                        break
                
                if not collision:
                    # Calculate distance to player from this position
                    distance = abs(new_x - player_x) + abs(new_y - player_y)
                    if distance < best_distance:
                        best_distance = distance
                        best_move = (new_x, new_y)
        
        # Move to best available position
        if best_move and best_distance <= current_distance:
            self.x, self.y = best_move
    
    def patrol_behavior(self, dungeon_map, other_enemies): # Patrol behavior for enemies
        if not hasattr(self, 'original_x'):
            # Store original position for patrol center
            self.original_x = self.x
            self.original_y = self.y
            self.patrol_direction = random.choice([(0, 1), (0, -1), (1, 0), (-1, 0)])
            self.patrol_steps = 0
            self.max_patrol_steps = random.randint(3, 6)
        
        # Change direction occasionally or when hitting obstacle
        if (self.patrol_steps >= self.max_patrol_steps or 
            random.random() < 0.1):  # 10% chance to change direction each move
            self.patrol_direction = random.choice([(0, 1), (0, -1), (1, 0), (-1, 0)])
            self.patrol_steps = 0
            self.max_patrol_steps = random.randint(3, 6)
        
        # Try to move in patrol direction
        new_x = self.x + self.patrol_direction[0]
        new_y = self.y + self.patrol_direction[1]
        
        # Check if new position is valid and within patrol range
        distance_from_origin = abs(new_x - self.original_x) + abs(new_y - self.original_y)
        
        if (0 <= new_x < len(dungeon_map[0]) and 
            0 <= new_y < len(dungeon_map) and 
            dungeon_map[new_y][new_x] != CellType.WALL and
            distance_from_origin <= ENEMY_PATROL_RANGE):
            
            # Check collision with other enemies
            collision = False
            for other_enemy in other_enemies:
                if (other_enemy != self and other_enemy.alive and 
                    other_enemy.x == new_x and other_enemy.y == new_y):
                    collision = True
                    break
            
            if not collision:
                self.x, self.y = new_x, new_y
                self.patrol_steps += 1
            else:
                # Change direction when blocked by other enemy
                self.patrol_direction = random.choice([(0, 1), (0, -1), (1, 0), (-1, 0)])
                self.patrol_steps = 0
        else:
            # Hit boundary or obstacle, change direction
            self.patrol_direction = random.choice([(0, 1), (0, -1), (1, 0), (-1, 0)])
            self.patrol_steps = 0

    def update_attack_timer(self, player_x, player_y, player, dungeon_map, projectiles_list): # When did enemies will attack player
        if not self.can_attack_player(player_x, player_y):
            self.attack_timer = 0
            return False
        
        if self.attack_timer <= 0:
            if self.is_ranged:
                # Ranged attack - create projectile
                if self.has_line_of_sight(player_x, player_y, dungeon_map):
                    projectile = self.create_projectile_to_player(player_x, player_y)
                    projectiles_list.append(projectile)
                    self.attack_timer = 60  # 1 second cooldown
            else:
                # Melee attack - direct damage if adjacent
                distance = abs(self.x - player_x) + abs(self.y - player_y)
                if distance == 1:  # Adjacent
                    player_died = player.take_damage(self.damage)
                    self.attack_timer = 30  # 0.5 second cooldown
                    return player_died
        else:
            self.attack_timer -= 1

        return False
    
    def can_attack_player(self, player_x, player_y): # Check did enemies can attack player
        distance = abs(self.x - player_x) + abs(self.y - player_y)
        return distance <= self.attack_range

    def has_line_of_sight(self, target_x, target_y, dungeon_map): # Check if enemies has vision to player
        if not self.is_ranged:
            return True  # Melee enemies don't need line of sight check
        
        # Simple line of sight - no walls between enemy and target
        dx = target_x - self.x
        dy = target_y - self.y
        
        # Check each step along the line
        steps = max(abs(dx), abs(dy))
        if steps == 0:
            return True
        
        for i in range(1, steps):
            check_x = self.x + (dx * i // steps)
            check_y = self.y + (dy * i // steps)
            
            if (0 <= check_x < len(dungeon_map[0]) and 
                0 <= check_y < len(dungeon_map) and
                dungeon_map[check_y][check_x] == CellType.WALL):
                return False
        
        return True

    def create_projectile_to_player(self, player_x, player_y): # Create projectile into player positon
        # Calculate direction
        dx = player_x - self.x
        dy = player_y - self.y
        
        # Normalize direction
        distance = math.sqrt(dx*dx + dy*dy)
        if distance > 0:
            dx /= distance
            dy /= distance
        
        # Create projectile from enemy position (convert to pixel coordinates)
        proj_x = self.x * 25 + 12.5
        proj_y = self.y * 25 + 12.5
        
        return Projectile(proj_x, proj_y, dx, dy, speed=3, is_enemy_projectile=True)

class Projectile:
    def __init__(self, x, y, direction_x, direction_y, speed=5, is_enemy_projectile=False):
        self.x = x
        self.y = y
        self.direction_x = direction_x
        self.direction_y = direction_y
        self.speed = speed
        self.active = True
        self.is_enemy_projectile = is_enemy_projectile
        
    def update(self, dungeon_map):
        # Move projectile
        self.x += self.direction_x * self.speed
        self.y += self.direction_y * self.speed
        
        # Check bounds and wall collision
        map_width = len(dungeon_map[0]) * 25  # cell_size = 25
        map_height = len(dungeon_map) * 25
        
        if (self.x < 0 or self.x >= map_width or 
            self.y < 0 or self.y >= map_height):
            self.active = False
            return
        
        # Check wall collision
        grid_x = int(self.x // 25)
        grid_y = int(self.y // 25)
        
        if (0 <= grid_x < len(dungeon_map[0]) and 
            0 <= grid_y < len(dungeon_map)):
            if dungeon_map[grid_y][grid_x] == CellType.WALL:
                self.active = False