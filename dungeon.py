import pygame
import sys
import random
from enum import Enum
from collections import defaultdict, deque
from heapq import heappush, heappop
import math
import pygame.mixer

from constants import *

class DungeonNode:
    def __init__(self, node_id, name, difficulty=1, required_nodes=None):
        self.id = node_id
        self.name = name
        self.difficulty = difficulty
        self.required_nodes = required_nodes or []
        self.completed = False
        self.unlocked = False
        self.position = (0, 0)  # Position on map view
        self.dungeon_map = None
        self.enemies_count = 0
        self.treasures_collected = 0
        self.total_treasures = 0

class DungeonGenerator:
    @staticmethod
    def generate_dungeon(width, height, difficulty):
        dungeon = [[CellType.WALL for _ in range(width)] for _ in range(height)]
        
        # Create rooms using simple room generation
        rooms = []
        for _ in range(3 + difficulty):
            room_width = random.randint(4, 8)
            room_height = random.randint(4, 8)
            room_x = random.randint(1, width - room_width - 1)
            room_y = random.randint(1, height - room_height - 1)
            
            # Create room
            for y in range(room_y, room_y + room_height):
                for x in range(room_x, room_x + room_width):
                    dungeon[y][x] = CellType.EMPTY
            
            rooms.append((room_x, room_y, room_width, room_height))
        
        # Connect rooms with corridors
        for i in range(len(rooms) - 1):
            x1 = rooms[i][0] + rooms[i][2] // 2
            y1 = rooms[i][1] + rooms[i][3] // 2
            x2 = rooms[i + 1][0] + rooms[i + 1][2] // 2
            y2 = rooms[i + 1][1] + rooms[i + 1][3] // 2
            
            # Horizontal corridor
            for x in range(min(x1, x2), max(x1, x2) + 1):
                if 0 <= x < width and 0 <= y1 < height:
                    dungeon[y1][x] = CellType.EMPTY
            
            # Vertical corridor
            for y in range(min(y1, y2), max(y1, y2) + 1):
                if 0 <= x2 < width and 0 <= y < height:
                    dungeon[y][x2] = CellType.EMPTY

        # Place treasures - ONLY in rooms, not in corridors (fix after spawn outside playable area)
        treasure_count = 2 + difficulty
        placed_treasures = 0
        max_attempts = 50 # is this still need ???? 90% not, but to make sure its here

        for room in rooms:
            if placed_treasures >= treasure_count:
                break
            
            # Try multiple times to place treasure in this room
            attempts = 0
            while attempts < 10 and placed_treasures < treasure_count:
                # Place treasure within room bounds (not on edges)
                x = random.randint(room[0] + 1, room[0] + room[2] - 2)
                y = random.randint(room[1] + 1, room[1] + room[3] - 2)
                
                # Make sure it's actually an empty cell and within bounds
                if (0 <= x < width and 0 <= y < height and 
                    dungeon[y][x] == CellType.EMPTY):
                    dungeon[y][x] = CellType.TREASURE
                    placed_treasures += 1
                    break
                
                attempts += 1

        # If still not enough treasures, force place them in any available room space
        if placed_treasures < treasure_count:
            for room in rooms:
                if placed_treasures >= treasure_count:
                    break
                    
                for dy in range(1, room[3] - 1):
                    for dx in range(1, room[2] - 1):
                        if placed_treasures >= treasure_count:
                            break
                            
                        x = room[0] + dx
                        y = room[1] + dy
                        
                        if (0 <= x < width and 0 <= y < height and 
                            dungeon[y][x] == CellType.EMPTY):
                            dungeon[y][x] = CellType.TREASURE
                            placed_treasures += 1
        
        # Place exit in last room
        if rooms:
            last_room = rooms[-1]
            exit_x = last_room[0] + last_room[2] - 2
            exit_y = last_room[1] + last_room[3] - 2
            dungeon[exit_y][exit_x] = CellType.EXIT
        
        return dungeon, treasure_count
