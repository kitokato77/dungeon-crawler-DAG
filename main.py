import pygame
import sys
import random
from enum import Enum
from collections import defaultdict, deque
from heapq import heappush, heappop
import math

from game import DungeonCrawlerGame

# Initialize Pygame
pygame.init()

# Run the game
if __name__ == "__main__":
    game = DungeonCrawlerGame()
    game.run()