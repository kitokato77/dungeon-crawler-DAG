import pygame
import sys
import random
from enum import Enum
from collections import defaultdict, deque
from heapq import heappush, heappop
import math

from dungeon import DungeonNode

class DAGManager:
    def __init__(self):
        self.nodes = {}
        self.adjacency_list = defaultdict(list)
        self.reverse_adjacency = defaultdict(list)
    
    def add_node(self, node):
        self.nodes[node.id] = node
        
    def add_edge(self, from_node_id, to_node_id):
        self.adjacency_list[from_node_id].append(to_node_id)
        self.reverse_adjacency[to_node_id].append(from_node_id)
        
    def update_unlocked_nodes(self):
        # Start node is always unlocked
        if 'start' in self.nodes:
            self.nodes['start'].unlocked = True
            
        # BFS to unlock nodes based on completed dependencies
        queue = deque(['start'])
        visited = set(['start'])
        
        while queue:
            current_id = queue.popleft()
            current_node = self.nodes[current_id]
            
            # Check all nodes that depend on current node
            for next_id in self.adjacency_list[current_id]:
                if next_id not in visited:
                    next_node = self.nodes[next_id]
                    
                    # Check if all required nodes are completed
                    all_requirements_met = True
                    for req_id in self.reverse_adjacency[next_id]:
                        if not self.nodes[req_id].completed:
                            all_requirements_met = False
                            break
                    
                    if all_requirements_met:
                        next_node.unlocked = True
                        if next_node.completed:
                            queue.append(next_id)
                            visited.add(next_id)