import pygame
import sys
import random
from enum import Enum
from collections import defaultdict, deque
from heapq import heappush, heappop
import math
import pygame.mixer

# Constants
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 768
FPS = 60

# AI Constants
ENEMY_DETECTION_RANGE = 8
ENEMY_PATROL_RANGE = 3

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
LIGHT_GRAY = (192, 192, 192)
BROWN = (139, 69, 19)
LIGHT_BLUE = (135, 206, 250)
DARK_BLUE = (30, 144, 255)
LIGHT_GREEN = (144, 238, 144)
DARK_GREEN = (34, 139, 34)
LIGHT_GRAY = (211, 211, 211)
MEDIUM_GRAY = (128, 128, 128)
PURPLE = (138, 43, 226)
GOLD = (255, 215, 0)
SILVER = (192, 192, 192)
BRONZE = (205, 127, 50)
CREAM = (255, 253, 208)
LIGHT_ORANGE = (255, 218, 185)

# Gradient colors for backgrounds
SKY_BLUE = (135, 206, 235)
PALE_BLUE = (176, 224, 230)
MINT_GREEN = (245, 255, 250)

# Enemy Colors
ENEMY_GOBLIN = (255, 0, 0) 
ENEMY_ORC = (139, 0, 0) 
ENEMY_ARCHER = (255, 165, 0)
ENEMY_MAGE = (128, 0, 128)
ENEMY_BOSS = (0, 0, 0) 

# Enemy projectile color
ENEMY_PROJECTILE = (255, 0, 255)

class GameState(Enum):
    MAP_VIEW = 1
    DUNGEON = 2
    VICTORY = 3
    GAME_OVER = 4

class CellType(Enum):
    EMPTY = 0
    WALL = 1
    PLAYER = 2
    ENEMY = 3
    TREASURE = 4
    EXIT = 5
