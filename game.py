import pygame
import sys
import random
from enum import Enum
from collections import defaultdict, deque
from heapq import heappush, heappop
import math
import pygame.mixer
import os

from constants import *
from entities import Player, Enemy, Projectile
from dungeon import DungeonGenerator
from dag_manager import DAGManager
from dungeon import DungeonNode

def resource_path(relative_path): # For path into asset file
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class DungeonCrawlerGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Dungeon Crawler - DAG Level System")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 48)
        self.credit_font = pygame.font.Font(None, 24)
        
        self.game_state = GameState.MAP_VIEW
        self.dag_manager = DAGManager()
        self.current_node = None
        self.player = None
        self.enemies = []
        self.dungeon_map = None
        self.camera_x = 0
        self.camera_y = 0
        self.projectiles = []
        self.enemy_projectiles = []
        self.last_direction = (0, -1)

        pygame.mixer.init()

        self.sounds = {
            "map_music": resource_path("assets/map.mp3"),
            "battle_music": resource_path("assets/battle.mp3"),
            "button_click": pygame.mixer.Sound(resource_path("assets/buttonclick.wav")),
            "enemy_attack": pygame.mixer.Sound(resource_path("assets/enemiesatt.wav")),
            "player_attack": pygame.mixer.Sound(resource_path("assets/playeratt.wav")),
            "collect_treasure": pygame.mixer.Sound(resource_path("assets/collecttre.wav")),
        }

        self.map_music_pos = 0

        self.setup_dag()

        pygame.mixer.music.load(self.sounds["map_music"])
        pygame.mixer.music.play(-1)  # Loop forever

    def draw_gradient_background(self, surface, color1, color2, vertical=True): # Draw background gradient
        if vertical:
            for y in range(SCREEN_HEIGHT):
                ratio = y / SCREEN_HEIGHT
                r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
                g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
                b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
                pygame.draw.line(surface, (r, g, b), (0, y), (SCREEN_WIDTH, y))
        else:
            for x in range(SCREEN_WIDTH):
                ratio = x / SCREEN_WIDTH
                r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
                g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
                b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
                pygame.draw.line(surface, (r, g, b), (x, 0), (x, SCREEN_HEIGHT))

    def draw_fancy_button(self, surface, x, y, width, height, text, color, text_color=WHITE, border_color=None): # Draw Fancy Button with shadow
        # Shadow
        shadow_rect = pygame.Rect(x + 3, y + 3, width, height)
        pygame.draw.rect(surface, (50, 50, 50), shadow_rect, border_radius=10)
        
        # Main button
        button_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(surface, color, button_rect, border_radius=10)
        
        # Highlight on top
        highlight_rect = pygame.Rect(x, y, width, height // 3)
        highlight_color = tuple(min(255, c + 30) for c in color)
        pygame.draw.rect(surface, highlight_color, highlight_rect, border_radius=10)
        
        # Border
        if border_color:
            pygame.draw.rect(surface, border_color, button_rect, 3, border_radius=10)
        
        # Text
        text_surface = self.font.render(text, True, text_color)
        text_rect = text_surface.get_rect(center=(x + width // 2, y + height // 2))
        surface.blit(text_surface, text_rect)
        
        return button_rect

    def draw_health_bar_fancy(self, surface, x, y, width, height, current, maximum, label="Health"): # Draw fancy health bar
        border_thickness = 6
        radius = height // 2 + border_thickness

        # Outer border
        outer_rect = pygame.Rect(x - border_thickness, y - border_thickness,
                                width + 2 * border_thickness, height + 2 * border_thickness)
        pygame.draw.rect(surface, WHITE, outer_rect, border_radius=radius)

        # Background
        bg_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(surface, DARK_GRAY, bg_rect, border_radius=height//2)

        # Health bar gradient
        health_ratio = current / maximum
        health_width = int(width * health_ratio)

        if health_width > 0:
            if health_ratio > 0.6:
                color1, color2 = LIGHT_GREEN, DARK_GREEN
            elif health_ratio > 0.3:
                color1, color2 = YELLOW, GOLD
            else:
                color1, color2 = ORANGE, RED

            for i in range(health_width):
                ratio = i / width
                r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
                g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
                b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
                pygame.draw.line(surface, (r, g, b), (x + i, y + 2), (x + i, y + height - 2))

        # Value text (centered inside bar): only "25/25"
        value_text = f"{current}/{maximum}"
        value_surface = self.font.render(value_text, True, BLACK)
        value_rect = value_surface.get_rect(center=(x + width // 2, y + height // 2))
        surface.blit(value_surface, value_rect)

        # Optional: small label above bar
        label_surface = self.font.render(label, True, WHITE)
        label_rect = label_surface.get_rect(center=(x + width // 2, y - 10))
        surface.blit(label_surface, label_rect)

    def setup_dag(self):
        # Generate random dungeon structure
        dungeons = self.generate_random_dag()
        dependencies = self.generate_random_dependencies(dungeons)
        positions = self.generate_random_positions(dungeons, dependencies)
        
        # Clear existing DAG
        self.dag_manager = DAGManager()
        
        # Add nodes to DAG
        for dungeon_id, name, difficulty in dungeons:
            node = DungeonNode(dungeon_id, name, difficulty, dependencies[dungeon_id])
            self.dag_manager.add_node(node)
            
            # Add edges based on dependencies
            for dep in dependencies[dungeon_id]:
                self.dag_manager.add_edge(dep, dungeon_id)

        # Generate and improve positions
        positions = self.generate_random_positions(dungeons, dependencies)
        improved_positions = self.improve_node_layout(positions, dependencies)

        # Apply improved positions to nodes
        for dungeon_id, position in improved_positions.items():
            self.dag_manager.nodes[dungeon_id].position = position
                
        # Update initial unlocked state
        self.dag_manager.update_unlocked_nodes()

    def generate_random_dag(self): # Generate random DAG structure for dungeons
        # Define possible dungeon themes and names
        dungeon_themes = [
            ("Cave", ["Dark Cave", "Crystal Cave", "Shadow Cave", "Ice Cave", "Lava Cave"]),
            ("Temple", ["Ancient Temple", "Sacred Chamber", "Mystic Shrine", "Lost Temple", "Forbidden Sanctum"]),
            ("Fortress", ["Goblin Fortress", "Orc Keep", "Bandit Stronghold", "Ruined Fort", "Stone Citadel"]),
            ("Underground", ["Underground Lake", "Sunken Ruins", "Flooded Cavern", "Deep Tunnels", "Forgotten Depths"]),
            ("Forest", ["Enchanted Grove", "Dark Forest", "Twisted Woods", "Elder Tree", "Fairy Ring"]),
            ("Desert", ["Sand Tomb", "Mirage Palace", "Scorching Dunes", "Oasis Temple", "Pyramid Chamber"])
        ]
        
        # Generate 6-10 dungeons randomly
        num_dungeons = random.randint(6, 10)
        dungeons = []
        used_names = set()
        
        # Always start with an entrance
        dungeons.append(("start", "Entrance Hall", 1))
        used_names.add("Entrance Hall")
        
        # Generate random dungeons
        for i in range(1, num_dungeons - 1):  # -1 because we'll add boss at the end
            theme_name, names = random.choice(dungeon_themes)
            available_names = [name for name in names if name not in used_names]
            
            if available_names:
                name = random.choice(available_names)
                used_names.add(name)
            else:
                # Fallback if all names used
                name = f"{theme_name} {i}"
            
            difficulty = min(5, 1 + (i // 2))  # Gradually increase difficulty
            dungeons.append((f"dungeon_{i}", name, difficulty))
        
        # Always end with a boss
        boss_names = ["Dragon's Lair", "Demon King's Throne", "Ancient Evil", "Dark Lord's Chamber", "Final Boss"]
        boss_name = random.choice(boss_names)
        dungeons.append(("boss", boss_name, 5))
        
        return dungeons

    def generate_random_dependencies(self, dungeons): # Generate random but logical dependencies
        dependencies = {}
        
        # Start has no dependencies
        dependencies["start"] = []
        
        # Create layers for logical progression
        num_dungeons = len(dungeons)
        layers = []
        
        # Layer 1: Depends only on start (2-3 dungeons)
        layer1_size = min(3, max(2, num_dungeons // 3))
        layer1 = [dungeons[i][0] for i in range(1, layer1_size + 1)]
        layers.append(layer1)
        
        # Layer 2: Depends on layer 1 (2-3 dungeons)
        remaining = num_dungeons - layer1_size - 2  # -2 for start and boss
        layer2_size = max(1, remaining // 2)
        layer2 = [dungeons[i][0] for i in range(layer1_size + 1, layer1_size + layer2_size + 1)]
        layers.append(layer2)
        
        # Layer 3: Remaining dungeons (except boss)
        layer3 = [dungeons[i][0] for i in range(layer1_size + layer2_size + 1, num_dungeons - 1)]
        if layer3:
            layers.append(layer3)
        
        # Boss layer
        layers.append(["boss"])
        
        # Set dependencies
        for layer_idx, layer in enumerate(layers):
            for dungeon_id in layer:
                if layer_idx == 0:
                    # First layer depends on start
                    dependencies[dungeon_id] = ["start"]
                else:
                    # Later layers depend on previous layer(s)
                    prev_layer = layers[layer_idx - 1]
                    
                    # Randomly choose 1-2 dependencies from previous layer
                    num_deps = random.randint(1, min(2, len(prev_layer)))
                    deps = random.sample(prev_layer, num_deps)
                    dependencies[dungeon_id] = deps
        
        return dependencies

    def generate_random_positions(self, dungeons, dependencies): # Make sure position tree logical
        positions = {}
        
        # Group dungeons by dependency depth
        depths = {}
        queue = deque()
        
        # Find root nodes (no dependencies)
        for dungeon_id, name, difficulty in dungeons:
            if not dependencies[dungeon_id]:
                depths[dungeon_id] = 0
                queue.append(dungeon_id)
        
        # Calculate depth for each node using BFS
        while queue:
            current_id = queue.popleft()
            current_depth = depths[current_id]
            
            # Find all nodes that depend on current node
            for next_id, deps in dependencies.items():
                if current_id in deps and next_id not in depths:
                    # Check if all dependencies are processed
                    all_deps_processed = all(dep in depths for dep in deps)
                    if all_deps_processed:
                        depths[next_id] = max(depths[dep] for dep in deps) + 1
                        queue.append(next_id)
        
        # Group nodes by depth
        depth_groups = defaultdict(list)
        for dungeon_id, depth in depths.items():
            depth_groups[depth].append(dungeon_id)
        
        # Calculate positions
        max_depth = max(depths.values()) if depths else 0
        vertical_spacing = (SCREEN_HEIGHT - 250) / (max_depth + 1)  # Leave margins
        
        for depth, nodes in depth_groups.items():
            y = 200 + depth * vertical_spacing
            
            if len(nodes) == 1:
                # Single node - center horizontally
                x = SCREEN_WIDTH // 2
                positions[nodes[0]] = (x, y)
            else:
                # Multiple nodes - distribute evenly across width
                if len(nodes) == 2:
                    # Special case for 2 nodes - better spacing
                    positions[nodes[0]] = (SCREEN_WIDTH // 3, y)
                    positions[nodes[1]] = (2 * SCREEN_WIDTH // 3, y)
                else:
                    # General case for multiple nodes
                    margin = 150
                    available_width = SCREEN_WIDTH - 2 * margin
                    spacing = available_width / (len(nodes) - 1) if len(nodes) > 1 else 0
                    
                    for i, node_id in enumerate(nodes):
                        if len(nodes) == 1:
                            x = SCREEN_WIDTH // 2
                        else:
                            x = margin + i * spacing
                        positions[node_id] = (x, y)
        
        return positions

    def improve_node_layout(self, positions, dependencies): # Improve node layout by minimizing edges and other
        improved_positions = positions.copy()
        
        # Group nodes by y-coordinate (depth level)
        levels = defaultdict(list)
        for node_id, (x, y) in positions.items():
            levels[y].append((node_id, x))
        
        # Sort nodes within each level and redistribute
        for y, nodes in levels.items():
            if len(nodes) <= 1:
                continue
                
            # Sort by dependencies - nodes with more connections get better positions
            def connection_count(node_id):
                incoming = len(dependencies.get(node_id, []))
                outgoing = len([1 for deps in dependencies.values() if node_id in deps])
                return incoming + outgoing
            
            nodes.sort(key=lambda item: connection_count(item[0]), reverse=True)
            
            # Redistribute positions
            if len(nodes) == 2:
                improved_positions[nodes[0][0]] = (SCREEN_WIDTH // 3, y)
                improved_positions[nodes[1][0]] = (2 * SCREEN_WIDTH // 3, y)
            else:
                margin = 120
                available_width = SCREEN_WIDTH - 2 * margin
                spacing = available_width / (len(nodes) - 1) if len(nodes) > 1 else 0
                
                for i, (node_id, _) in enumerate(nodes):
                    x = margin + i * spacing
                    improved_positions[node_id] = (x, y)
        
        return improved_positions

    def enter_dungeon(self, node_id):
        node = self.dag_manager.nodes[node_id]
        if not node.unlocked:
            return
        
        # Pause map music and remember position
        self.map_music_pos = pygame.mixer.music.get_pos()
        pygame.mixer.music.stop()

        # Play battle music
        pygame.mixer.music.load(self.sounds["battle_music"])
        pygame.mixer.music.set_volume(0.7)
        pygame.mixer.music.play(-1)

            
        self.current_node = node
        self.game_state = GameState.DUNGEON
        
        # Generate dungeon if not exists
        if node.dungeon_map is None:
            dungeon_map, treasure_count = DungeonGenerator.generate_dungeon(25, 20, node.difficulty)
            node.dungeon_map = dungeon_map
            node.total_treasures = treasure_count
            node.treasures_collected = 0
            
            # Create enemies
            self.enemies = []
            enemy_types_by_level = {
                1: ["goblin"],
                2: ["goblin", "orc"],
                3: ["goblin", "orc", "archer"],
                4: ["goblin", "orc", "archer", "mage"],
                5: ["goblin", "orc", "archer", "mage", "boss"]
            }

            available_types = enemy_types_by_level.get(node.difficulty, ["goblin"])
            enemy_count = 2 + node.difficulty

            # Ensure boss only appears once in level 5
            boss_added = False

            # Find player starting position first
            player_start_x, player_start_y = None, None
            for y in range(len(dungeon_map)):
                for x in range(len(dungeon_map[0])):
                    if dungeon_map[y][x] == CellType.EMPTY:
                        player_start_x, player_start_y = x, y
                        break
                if player_start_x is not None:
                    break

            # Create enemies with minimum distance from player - ONLY in playable areas
            for _ in range(enemy_count):
                attempts = 0
                enemy_placed = False
                
                # First try to place in rooms (preferred)
                while attempts < 50 and not enemy_placed:
                    # Try to place in a random room first
                    if hasattr(self, 'current_rooms') or True:  # We'll get rooms from generator
                        # Find all empty cells in playable area
                        empty_cells = []
                        for y in range(len(dungeon_map)):
                            for x in range(len(dungeon_map[0])):
                                if dungeon_map[y][x] == CellType.EMPTY:
                                    # Check if it's reasonably accessible (not in tiny isolated areas)
                                    adjacent_empty = 0
                                    for dx, dy in [(0,1), (0,-1), (1,0), (-1,0)]:
                                        nx, ny = x + dx, y + dy
                                        if (0 <= nx < len(dungeon_map[0]) and 
                                            0 <= ny < len(dungeon_map) and 
                                            dungeon_map[ny][nx] == CellType.EMPTY):
                                            adjacent_empty += 1
                                    
                                    # Only consider cells with at least 2 adjacent empty spaces
                                    if adjacent_empty >= 2:
                                        empty_cells.append((x, y))
                        
                        if empty_cells:
                            x, y = random.choice(empty_cells)
                            
                            # Calculate distance from player start position
                            if player_start_x is not None and player_start_y is not None:
                                distance = abs(x - player_start_x) + abs(y - player_start_y)
                                if distance >= 5:  # Minimum 5 blocks away
                                    # TAMBAHKAN KODE ANDA DI SINI:
                                    enemy_type = random.choice(available_types)
                                    
                                    # Special handling for boss
                                    if enemy_type == "boss":
                                        if boss_added or node.difficulty < 5:
                                            enemy_type = random.choice(["goblin", "orc", "archer", "mage"])
                                        else:
                                            boss_added = True
                                    
                                    self.enemies.append(Enemy(x, y, enemy_type, node.difficulty))
                                    enemy_placed = True
                            else:
                                # Fallback if no player position found
                                # TAMBAHKAN KODE ANDA DI SINI JUGA:
                                enemy_type = random.choice(available_types)
                                
                                # Special handling for boss
                                if enemy_type == "boss":
                                    if boss_added or node.difficulty < 5:
                                        enemy_type = random.choice(["goblin", "orc", "archer", "mage"])
                                    else:
                                        boss_added = True
                                
                                self.enemies.append(Enemy(x, y, enemy_type, node.difficulty))
                                enemy_placed = True
                    
                    attempts += 1
                
                # If couldn't place enemy in good location, try any valid empty space
                if not enemy_placed:
                    for y in range(1, len(dungeon_map) - 1):  # Avoid edges
                        for x in range(1, len(dungeon_map[0]) - 1):  # Avoid edges
                            if dungeon_map[y][x] == CellType.EMPTY:
                                # Check if position has access (not isolated)
                                accessible = False
                                for dx, dy in [(0,1), (0,-1), (1,0), (-1,0)]:
                                    nx, ny = x + dx, y + dy
                                    if (0 <= nx < len(dungeon_map[0]) and 
                                        0 <= ny < len(dungeon_map) and 
                                        dungeon_map[ny][nx] == CellType.EMPTY):
                                        accessible = True
                                        break
                                
                                if accessible:
                                    # TAMBAHKAN KODE ANDA DI SINI JUGA:
                                    enemy_type = random.choice(available_types)
                                    
                                    # Special handling for boss
                                    if enemy_type == "boss":
                                        if boss_added or node.difficulty < 5:
                                            enemy_type = random.choice(["goblin", "orc", "archer", "mage"])
                                        else:
                                            boss_added = True
                                    
                                    self.enemies.append(Enemy(x, y, enemy_type, node.difficulty))
                                    break
                        else:
                            continue
                        break

            node.enemies_count = len(self.enemies)
        else:
            # Restore existing state
            self.enemies = [e for e in self.enemies if e.alive]
        
        self.dungeon_map = node.dungeon_map
        
        # Place player at entrance (first empty cell)
        if self.player is None:
            self.player = Player(0, 0)
            
        # Find starting position
        for y in range(len(self.dungeon_map)):
            for x in range(len(self.dungeon_map[0])):
                if self.dungeon_map[y][x] == CellType.EMPTY:
                    self.player.x, self.player.y = x, y
                    break
            else:
                continue
            break
    
    def handle_events(self): # Handle event happen in the game
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if event.type == pygame.KEYDOWN:
                if self.game_state == GameState.MAP_VIEW:
                    self.handle_map_input(event.key)
                elif self.game_state == GameState.DUNGEON:
                    self.handle_dungeon_input(event.key)
                elif self.game_state == GameState.VICTORY:
                    if event.key == pygame.K_SPACE:
                        self.sounds["button_click"].play()
                        self.game_state = GameState.MAP_VIEW
                elif self.game_state == GameState.GAME_OVER:
                    if event.key == pygame.K_SPACE:
                        self.sounds["button_click"].play()
                        self.restart_game()
                    elif event.key == pygame.K_ESCAPE:
                        self.sounds["button_click"].play()
                        pygame.quit()
                        sys.exit()
            
            if event.type == pygame.MOUSEBUTTONDOWN and self.game_state == GameState.MAP_VIEW:
                self.sounds["button_click"].play()
                self.handle_map_click(event.pos)
        
        return True
    
    def handle_map_input(self, key):
        if key == pygame.K_ESCAPE:
            pygame.quit()
            sys.exit()
        elif key == pygame.K_r:  # Press R to regenerate map
            self.setup_dag()
    
    def handle_map_click(self, pos): # A bit useless but i think place it here
        mouse_x, mouse_y = pos
        
        for node in self.dag_manager.nodes.values():
            node_x, node_y = node.position
            distance = math.sqrt((mouse_x - node_x)**2 + (mouse_y - node_y)**2)
            
            if distance <= 30:  # Click radius
                if node.unlocked:
                    self.enter_dungeon(node.id)
                break
    
    def handle_dungeon_input(self, key):
        if key == pygame.K_ESCAPE:
            pygame.mixer.music.stop()  # Stop dungeon (battle) music

            # Resume map music from where it left off
            pygame.mixer.music.load(self.sounds["map_music"])
            pygame.mixer.music.set_volume(1.0)
            pygame.mixer.music.play(-1, start=self.map_music_pos / 1000.0)

            self.game_state = GameState.MAP_VIEW
        elif key == pygame.K_UP:
            self.player.move(0, -1, self.dungeon_map, self.enemies)
            self.last_direction = (0, -1)
        elif key == pygame.K_DOWN:
            self.player.move(0, 1, self.dungeon_map, self.enemies)
            self.last_direction = (0, 1)
        elif key == pygame.K_LEFT:
            self.player.move(-1, 0, self.dungeon_map, self.enemies)
            self.last_direction = (-1, 0)
        elif key == pygame.K_RIGHT:
            self.player.move(1, 0, self.dungeon_map, self.enemies)
            self.last_direction = (1, 0)
        elif key == pygame.K_SPACE:
            self.shoot_projectile()
    
        keys = pygame.key.get_pressed()
        if sum([keys[pygame.K_UP], keys[pygame.K_DOWN], keys[pygame.K_LEFT], keys[pygame.K_RIGHT]]) > 1:
            # Make sure there's no extra move if pressed two button at the same time and it will count as one move per keys
            pass
    
    def shoot_projectile(self): # Shooting goes brrrr
        keys = pygame.key.get_pressed()
        self.sounds["player_attack"].play()
        
        # Determine direction based on current key press
        direction_x, direction_y = 0, 0
        
        if keys[pygame.K_UP]:
            direction_y = -1
            self.last_direction = (0, -1)
        elif keys[pygame.K_DOWN]:
            direction_y = 1
            self.last_direction = (0, 1)
        elif keys[pygame.K_LEFT]:
            direction_x = -1
            self.last_direction = (-1, 0)
        elif keys[pygame.K_RIGHT]:
            direction_x = 1
            self.last_direction = (1, 0)
        else:
            # If no direction key is pressed, use last direction
            if hasattr(self, 'last_direction'):
                direction_x, direction_y = self.last_direction
            else:
                direction_x, direction_y = 0, -1  # Default up
        
        if direction_x != 0 or direction_y != 0:
            # Create projectile from player position (convert grid to pixel coordinates)
            proj_x = self.player.x * 25 + 12.5  # Center of cell
            proj_y = self.player.y * 25 + 12.5
            
            # Fix : Using correct parameter
            projectile = Projectile(proj_x, proj_y, direction_x, direction_y, speed=5, is_enemy_projectile=False)
            self.projectiles.append(projectile)

    def update_projectiles(self):
        for projectile in self.projectiles[:]:  # Copy list for safety iteration
            if not projectile.active:
                self.projectiles.remove(projectile)
                continue
                
            projectile.update(self.dungeon_map)
            
            if not projectile.active:
                continue
            
            # Check collision with enemies
            proj_grid_x = int(projectile.x // 25)
            proj_grid_y = int(projectile.y // 25)
            
            for enemy in self.enemies:
                if enemy.alive and enemy.x == proj_grid_x and enemy.y == proj_grid_y:
                    # Hit enemy
                    enemy.alive = False
                    projectile.active = False
                    self.player.gain_experience(25)
                    break
        
        # Remove inactive projectiles
        self.projectiles = [p for p in self.projectiles if p.active]

    def draw_projectiles(self):
        # Player projectiles with glow effect
        for projectile in self.projectiles:
            if projectile.active:
                screen_x = projectile.x - self.camera_x
                screen_y = projectile.y - self.camera_y
                
                if (-10 <= screen_x <= SCREEN_WIDTH + 10 and 
                    -10 <= screen_y <= SCREEN_HEIGHT + 10):
                    # Glow effect
                    pygame.draw.circle(self.screen, LIGHT_BLUE, (int(screen_x), int(screen_y)), 5)
                    pygame.draw.circle(self.screen, DARK_BLUE, (int(screen_x), int(screen_y)), 3)
                    pygame.draw.circle(self.screen, WHITE, (int(screen_x), int(screen_y)), 2)
        
        # Enemy projectiles with different styling
        for projectile in self.enemy_projectiles:
            if projectile.active:
                screen_x = projectile.x - self.camera_x
                screen_y = projectile.y - self.camera_y
                
                if (-10 <= screen_x <= SCREEN_WIDTH + 10 and 
                    -10 <= screen_y <= SCREEN_HEIGHT + 10):
                    # Dark projectile with red glow
                    pygame.draw.circle(self.screen, RED, (int(screen_x), int(screen_y)), 5)
                    pygame.draw.circle(self.screen, DARK_GRAY, (int(screen_x), int(screen_y)), 3)
                    pygame.draw.circle(self.screen, WHITE, (int(screen_x), int(screen_y)), 1)
    
    def update_game(self):
        if self.game_state == GameState.DUNGEON:
            self.update_dungeon()
    
    def update_dungeon(self):
        # Check if player is dead first
        if self.player.health <= 0:
            self.game_state = GameState.GAME_OVER
            return
        
        # Update enemies
        for enemy in self.enemies:
            if enemy.alive:
                enemy.move_towards_player(self.player.x, self.player.y, self.dungeon_map, self.enemies)
                
                # Update attack timer and check for damage
                player_died = enemy.update_attack_timer(self.player.x, self.player.y, self.player, 
                                                        self.dungeon_map, self.enemy_projectiles, self.sounds)
                if player_died:
                    self.game_state = GameState.GAME_OVER
                    return

        self.update_projectiles()
        self.update_enemy_projectiles()
        
        # Check interactions
        player_x, player_y = self.player.x, self.player.y
        cell = self.dungeon_map[player_y][player_x]
        
        if cell == CellType.TREASURE:
            self.dungeon_map[player_y][player_x] = CellType.EMPTY
            self.current_node.treasures_collected += 1
            self.player.heal(20)
            self.player.gain_experience(10)
            self.sounds["collect_treasure"].play()
        
        # Check completion conditions
        alive_enemies = sum(1 for e in self.enemies if e.alive)
        if (self.current_node.treasures_collected >= self.current_node.total_treasures and 
            alive_enemies == 0):
            
            # Check if player is at exit
            if cell == CellType.EXIT:
                self.complete_dungeon()
        
        # Update camera
        self.update_camera()

    def update_enemy_projectiles(self): # Updating enemies projectiles inside the dungeon
        for projectile in self.enemy_projectiles[:]:
            if not projectile.active:
                self.enemy_projectiles.remove(projectile)
                continue
                
            projectile.update(self.dungeon_map)
            
            if not projectile.active:
                continue
            
            # Check collision with player
            proj_grid_x = int(projectile.x // 25)
            proj_grid_y = int(projectile.y // 25)
            
            if proj_grid_x == self.player.x and proj_grid_y == self.player.y:
                # Hit player
                player_died = self.player.take_damage(20)  # Enemy projectile damage
                projectile.active = False
                if player_died:
                    self.game_state = GameState.GAME_OVER
                    return
        
        # Remove inactive projectiles
        self.enemy_projectiles = [p for p in self.enemy_projectiles if p.active]

    def update_projectiles(self):
        # Changing method to check enemies health
        for projectile in self.projectiles[:]:
            if not projectile.active:
                self.projectiles.remove(projectile)
                continue
                
            projectile.update(self.dungeon_map)
            
            if not projectile.active:
                continue
            
            # Check collision with enemies
            proj_grid_x = int(projectile.x // 25)
            proj_grid_y = int(projectile.y // 25)
            
            for enemy in self.enemies:
                if enemy.alive and enemy.x == proj_grid_x and enemy.y == proj_grid_y:
                    # Hit enemy
                    enemy_died = enemy.take_damage(20)  # Player projectile damage
                    projectile.active = False
                    if enemy_died:
                        self.player.gain_experience(25)
                    break
        
        # Remove inactive projectiles
        self.projectiles = [p for p in self.projectiles if p.active]

    def complete_dungeon(self):
        self.current_node.completed = True
        self.dag_manager.update_unlocked_nodes()

        pygame.mixer.music.stop()
        pygame.mixer.music.load(self.sounds["map_music"])
        pygame.mixer.music.play(-1, start=self.map_music_pos / 1000.0)
        
        # Check if all nodes completed
        all_completed = all(node.completed for node in self.dag_manager.nodes.values())
        if all_completed:
            self.game_state = GameState.VICTORY
        else:
            self.game_state = GameState.MAP_VIEW

    def update_camera(self):
        # Center camera on map center instead of player
        if self.dungeon_map:
            cell_size = 25
            map_width = len(self.dungeon_map[0]) * cell_size
            map_height = len(self.dungeon_map) * cell_size
            
            self.camera_x = (map_width - SCREEN_WIDTH) // 2
            self.camera_y = (map_height - SCREEN_HEIGHT) // 2
        
    def restart_game(self):
        # Reset all nodes
        for node in self.dag_manager.nodes.values():
            node.completed = False
            node.unlocked = False
            node.dungeon_map = None
            node.enemies_count = 0
            node.treasures_collected = 0
            node.total_treasures = 0
        
        # Reset player
        self.player = None
        self.enemies = []
        self.current_node = None
        self.dungeon_map = None
        
        # Generate new DAG structure
        self.setup_dag()
        
        # Return to map view
        self.game_state = GameState.MAP_VIEW
    
    def draw_map_view(self):
        # Gradient background
        self.draw_gradient_background(self.screen, SKY_BLUE, PALE_BLUE)
        
        # Draw decorative border
        border_rect = pygame.Rect(10, 10, SCREEN_WIDTH - 20, SCREEN_HEIGHT - 20)
        pygame.draw.rect(self.screen, WHITE, border_rect, 5, border_radius=15)
        pygame.draw.rect(self.screen, DARK_BLUE, border_rect, 3, border_radius=15)
        
        # Draw title with shadow and glow effect
        title_text = "DUNGEON ADVENTURE MAP"
        
        # Title shadow
        shadow_surface = self.title_font.render(title_text, True, DARK_GRAY)
        shadow_rect = shadow_surface.get_rect(center=(SCREEN_WIDTH // 2 + 2, 52))
        self.screen.blit(shadow_surface, shadow_rect)
        
        # Main title
        title_surface = self.title_font.render(title_text, True, DARK_BLUE)
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, 50))
        self.screen.blit(title_surface, title_rect)
        
        # Subtitle
        subtitle_text = "Choose your next adventure!"
        subtitle_surface = self.font.render(subtitle_text, True, PURPLE)
        subtitle_rect = subtitle_surface.get_rect(center=(SCREEN_WIDTH // 2, 80))
        self.screen.blit(subtitle_surface, subtitle_rect)

        # Credit
        credit_text = self.credit_font.render("credit : kitokato77", True, (255, 255, 255))
        credit_rect = credit_text.get_rect(topright=(self.screen.get_width() -20, 15))
        self.screen.blit(credit_text, credit_rect)
        
        # Draw connections with better styling
        for from_id, to_ids in self.dag_manager.adjacency_list.items():
            from_node = self.dag_manager.nodes[from_id]
            for to_id in to_ids:
                to_node = self.dag_manager.nodes[to_id]
                
                if from_node.completed:
                    color = DARK_GREEN
                    width = 4
                elif from_node.unlocked:
                    color = GOLD
                    width = 3
                else:
                    color = MEDIUM_GRAY
                    width = 2
                
                # Draw line with glow effect
                pygame.draw.line(self.screen, color, from_node.position, to_node.position, width + 2)
                pygame.draw.line(self.screen, WHITE, from_node.position, to_node.position, width)
        
        # Draw nodes with fancy styling
        for node in self.dag_manager.nodes.values():
            x, y = node.position
            
            # Node shadow
            pygame.draw.circle(self.screen, (100, 100, 100), (int(x + 3), int(y + 3)), 33)
            
            # Determine node color and style
            if node.completed:
                main_color = LIGHT_GREEN
                border_color = DARK_GREEN
                inner_color = WHITE
                icon = ""
            elif node.unlocked:
                main_color = LIGHT_BLUE
                border_color = DARK_BLUE
                inner_color = YELLOW
                icon = ""
            else:
                main_color = LIGHT_GRAY
                border_color = MEDIUM_GRAY
                inner_color = WHITE
                icon = ""
            
            # Main node circle
            pygame.draw.circle(self.screen, main_color, (int(x), int(y)), 35)
            pygame.draw.circle(self.screen, border_color, (int(x), int(y)), 35, 4)
            pygame.draw.circle(self.screen, inner_color, (int(x), int(y)), 25)
            
            # Node icon
            icon_surface = self.font.render(icon, True, border_color)
            icon_rect = icon_surface.get_rect(center=(x, y))
            self.screen.blit(icon_surface, icon_rect)
            
            # Node name with background
            name_bg_rect = pygame.Rect(x - 80, y - 70, 160, 25)
            pygame.draw.rect(self.screen, CREAM, name_bg_rect, border_radius=12)
            pygame.draw.rect(self.screen, border_color, name_bg_rect, 2, border_radius=12)
            
            name_text = self.font.render(node.name, True, DARK_BLUE)
            name_rect = name_text.get_rect(center=(x, y - 57))
            self.screen.blit(name_text, name_rect)
            
            # Difficulty with stars
            stars = "" * node.difficulty
            diff_text = self.font.render(f"Level {node.difficulty} {stars}", True, GOLD)
            diff_rect = diff_text.get_rect(center=(x, y + 50))
            self.screen.blit(diff_text, diff_rect)
        
        # Fancy legend panel
        legend_panel = pygame.Rect(30, SCREEN_HEIGHT - 150, 300, 120)
        pygame.draw.rect(self.screen, CREAM, legend_panel, border_radius=15)
        pygame.draw.rect(self.screen, DARK_BLUE, legend_panel, 3, border_radius=15)
        
        legend_title = self.font.render("LEGEND", True, DARK_BLUE)
        self.screen.blit(legend_title, (50, SCREEN_HEIGHT - 140))
        
        # Legend items
        legend_items = [
            (LIGHT_GRAY, "Locked", SCREEN_HEIGHT - 115),
            (LIGHT_BLUE, "Available", SCREEN_HEIGHT - 90),
            (LIGHT_GREEN, "Completed", SCREEN_HEIGHT - 65)
        ]
        
        for color, text, y_pos in legend_items:
            pygame.draw.circle(self.screen, color, (60, y_pos), 12)
            pygame.draw.circle(self.screen, DARK_BLUE, (60, y_pos), 12, 2)
            legend_text = self.font.render(text, True, DARK_BLUE)
            self.screen.blit(legend_text, (85, y_pos - 10))
        
        # Instructions panel
        inst_panel = pygame.Rect(SCREEN_WIDTH - 420, SCREEN_HEIGHT - 100, 400, 80)
        pygame.draw.rect(self.screen, LIGHT_ORANGE, inst_panel, border_radius=15)
        pygame.draw.rect(self.screen, PURPLE, inst_panel, 3, border_radius=15)
        
        inst_title = self.font.render("CONTROLS", True, PURPLE)
        self.screen.blit(inst_title, (SCREEN_WIDTH - 400, SCREEN_HEIGHT - 90))
        
        inst_text1 = self.font.render("Click on available dungeons to enter", True, DARK_BLUE)
        self.screen.blit(inst_text1, (SCREEN_WIDTH - 410, SCREEN_HEIGHT - 65))
        
        inst_text2 = self.font.render("Press R to generate new map", True, DARK_BLUE)
        self.screen.blit(inst_text2, (SCREEN_WIDTH - 410, SCREEN_HEIGHT - 40))
    
    def draw_dungeon_view(self):
        # Light background instead of black
        self.screen.fill(MINT_GREEN)
        
        if self.dungeon_map is None:
            return
        
        cell_size = 25
        
        # Draw dungeon with better colors
        for y, row in enumerate(self.dungeon_map):
            for x, cell in enumerate(row):
                screen_x = x * cell_size - self.camera_x
                screen_y = y * cell_size - self.camera_y
                
                if -cell_size <= screen_x <= SCREEN_WIDTH and -cell_size <= screen_y <= SCREEN_HEIGHT:
                    rect = pygame.Rect(screen_x, screen_y, cell_size, cell_size)
                    
                    if cell == CellType.WALL:
                        pygame.draw.rect(self.screen, MEDIUM_GRAY, rect)
                        pygame.draw.rect(self.screen, DARK_GRAY, rect, 1)
                    elif cell == CellType.EMPTY:
                        pygame.draw.rect(self.screen, CREAM, rect)
                        pygame.draw.rect(self.screen, LIGHT_GRAY, rect, 1)
                    elif cell == CellType.TREASURE:
                        pygame.draw.rect(self.screen, CREAM, rect)
                        pygame.draw.rect(self.screen, GOLD, rect.inflate(-6, -6))
                        pygame.draw.rect(self.screen, YELLOW, rect.inflate(-10, -10))
                        # Add sparkle effect
                        center_x, center_y = rect.center
                        pygame.draw.circle(self.screen, WHITE, (center_x, center_y), 3)
                    elif cell == CellType.EXIT:
                        pygame.draw.rect(self.screen, CREAM, rect)
                        pygame.draw.rect(self.screen, LIGHT_GREEN, rect.inflate(-4, -4))
                        pygame.draw.rect(self.screen, DARK_GREEN, rect.inflate(-8, -8))
                        # Add exit arrow
                        center_x, center_y = rect.center
                        pygame.draw.polygon(self.screen, WHITE, [
                            (center_x, center_y - 5),
                            (center_x - 4, center_y + 3),
                            (center_x + 4, center_y + 3)
                        ])
        
        # Draw enemies with better styling
        for enemy in self.enemies:
            if enemy.alive:
                screen_x = enemy.x * cell_size - self.camera_x
                screen_y = enemy.y * cell_size - self.camera_y
                
                if -cell_size <= screen_x <= SCREEN_WIDTH and -cell_size <= screen_y <= SCREEN_HEIGHT:
                    center_x = screen_x + cell_size // 2
                    center_y = screen_y + cell_size // 2
                    
                    # Enemy shadow
                    pygame.draw.circle(self.screen, (100, 100, 100), 
                                    (center_x + 2, center_y + 2), cell_size // 3 + 2)
                    
                    # Enemy body
                    pygame.draw.circle(self.screen, enemy.color, 
                                    (center_x, center_y), cell_size // 3)
                    pygame.draw.circle(self.screen, WHITE, 
                                    (center_x, center_y), cell_size // 3, 2)
                    
                    # Enemy eyes
                    eye_size = 2
                    pygame.draw.circle(self.screen, RED, 
                                    (center_x - 3, center_y - 2), eye_size)
                    pygame.draw.circle(self.screen, RED, 
                                    (center_x + 3, center_y - 2), eye_size)
                    
                    # Health bar for stronger enemies  
                    if enemy.max_health > 20:
                        self.draw_health_bar_fancy(self.screen, screen_x, screen_y - 12, 
                                                cell_size, 6, enemy.health, enemy.max_health, "")
        
        self.draw_projectiles()
        
        # Draw player with better styling
        screen_x = self.player.x * cell_size - self.camera_x
        screen_y = self.player.y * cell_size - self.camera_y
        center_x = screen_x + cell_size // 2
        center_y = screen_y + cell_size // 2
        
        # Player shadow
        pygame.draw.circle(self.screen, (100, 100, 100), 
                        (center_x + 2, center_y + 2), cell_size // 3 + 2)
        
        # Player body
        pygame.draw.circle(self.screen, DARK_BLUE, (center_x, center_y), cell_size // 3)
        pygame.draw.circle(self.screen, LIGHT_BLUE, (center_x, center_y), cell_size // 3 - 2)
        pygame.draw.circle(self.screen, WHITE, (center_x, center_y), cell_size // 3, 2)
        
        # Player face
        pygame.draw.circle(self.screen, WHITE, (center_x - 2, center_y - 2), 1)
        pygame.draw.circle(self.screen, WHITE, (center_x + 2, center_y - 2), 1)
        pygame.draw.arc(self.screen, WHITE, (center_x - 3, center_y, 6, 4), 0, 3.14, 1)
        
        # Draw UI
        self.draw_dungeon_ui()
    
    def draw_dungeon_ui(self):
        # UI Panel background
        ui_panel = pygame.Rect(5, 5, 320, 140)
        pygame.draw.rect(self.screen, CREAM, ui_panel, border_radius=15)
        pygame.draw.rect(self.screen, DARK_BLUE, ui_panel, 3, border_radius=15)
        
        # Health bar
        self.draw_health_bar_fancy(self.screen, 15, 15, 200, 25, 
                                self.player.health, self.player.max_health, "Health")
        
        # Experience bar
        exp_needed = (self.player.level * 100)
        current_exp = self.player.experience % exp_needed if exp_needed > 0 else 0
        
        exp_bg = pygame.Rect(15, 50, 200, 20)
        pygame.draw.rect(self.screen, DARK_GRAY, exp_bg, border_radius=10)
        
        if exp_needed > 0:
            exp_ratio = current_exp / exp_needed
            exp_width = int(200 * exp_ratio)
            if exp_width > 0:
                exp_rect = pygame.Rect(15, 50, exp_width, 20)
                pygame.draw.rect(self.screen, PURPLE, exp_rect, border_radius=10)
        
        pygame.draw.rect(self.screen, WHITE, exp_bg, 2, border_radius=10)
        
        exp_text = f"Level {self.player.level} | XP: {current_exp}/{exp_needed}"
        exp_surface = self.font.render(exp_text, True, WHITE)
        exp_rect = exp_surface.get_rect(center=(115, 60))
        self.screen.blit(exp_surface, exp_rect)
        
        # Dungeon info
        dungeon_text = f"{self.current_node.name}"
        dungeon_surface = self.font.render(dungeon_text, True, DARK_BLUE)
        self.screen.blit(dungeon_surface, (15, 80))
        
        # Progress info
        alive_enemies = sum(1 for e in self.enemies if e.alive)
        progress_text = f"Treasures: {self.current_node.treasures_collected}/{self.current_node.total_treasures} | Enemies: {alive_enemies}"
        progress_surface = self.font.render(progress_text, True, DARK_BLUE)
        self.screen.blit(progress_surface, (15, 105))
        
        # Controls panel
        controls_panel = pygame.Rect(SCREEN_WIDTH - 320, 5, 315, 120)
        pygame.draw.rect(self.screen, LIGHT_ORANGE, controls_panel, border_radius=15)
        pygame.draw.rect(self.screen, PURPLE, controls_panel, 3, border_radius=15)
        
        controls_title = self.font.render("CONTROLS", True, PURPLE)
        self.screen.blit(controls_title, (SCREEN_WIDTH - 310, 15))
        
        controls = [
            "Arrow Keys: Move",
            "Space + Direction: Attack",
            "Escape: Return to map",
            "Goal: Clear all, reach exit!"
        ]
        
        for i, control in enumerate(controls):
            text_surface = self.font.render(control, True, DARK_BLUE)
            self.screen.blit(text_surface, (SCREEN_WIDTH - 310, 40 + i * 20))
    
    def draw_victory_screen(self):
        # Gradient background
        self.draw_gradient_background(self.screen, GOLD, YELLOW)
        
        # Victory banner
        banner_rect = pygame.Rect(SCREEN_WIDTH // 2 - 300, 100, 600, 100)
        pygame.draw.rect(self.screen, WHITE, banner_rect, border_radius=20)
        pygame.draw.rect(self.screen, GOLD, banner_rect, 5, border_radius=20)
        
        # Victory text with effects
        victory_text = "VICTORY!"
        victory_surface = self.title_font.render(victory_text, True, GOLD)
        victory_rect = victory_surface.get_rect(center=(SCREEN_WIDTH // 2, 120))
        self.screen.blit(victory_surface, victory_rect)
        
        crown_text = "DUNGEON MASTER"
        crown_surface = self.title_font.render(crown_text, True, PURPLE)
        crown_rect = crown_surface.get_rect(center=(SCREEN_WIDTH // 2, 170))
        self.screen.blit(crown_surface, crown_rect)
        
        # Completion message
        completion_text = "You have conquered all dungeons and become the ultimate adventurer!"
        completion_surface = self.font.render(completion_text, True, DARK_BLUE)
        completion_rect = completion_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.screen.blit(completion_surface, completion_rect)
        
        # Continue button
        self.draw_fancy_button(self.screen, SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 50, 
                            200, 40, "Space Return", LIGHT_BLUE, WHITE, DARK_BLUE)
    
    def draw_game_over_screen(self):
        # Dark gradient background
        self.draw_gradient_background(self.screen, (60, 60, 60), (30, 30, 30))
        
        # Game over panel
        panel_rect = pygame.Rect(SCREEN_WIDTH // 2 - 300, 150, 600, 300)
        pygame.draw.rect(self.screen, (40, 40, 40), panel_rect, border_radius=20)
        pygame.draw.rect(self.screen, RED, panel_rect, 5, border_radius=20)
        
        # Game Over text
        game_over_text = "GAME OVER"
        game_over_surface = self.title_font.render(game_over_text, True, RED)
        game_over_rect = game_over_surface.get_rect(center=(SCREEN_WIDTH // 2, 200))
        self.screen.blit(game_over_surface, game_over_rect)
        
        # Death message
        death_text = "Your adventure has come to an end..."
        death_surface = self.font.render(death_text, True, WHITE)
        death_rect = death_surface.get_rect(center=(SCREEN_WIDTH // 2, 250))
        self.screen.blit(death_surface, death_rect)
        
        # Show current dungeon
        if self.current_node:
            dungeon_text = f"Fallen in: {self.current_node.name}"
            dungeon_surface = self.font.render(dungeon_text, True, YELLOW)
            dungeon_rect = dungeon_surface.get_rect(center=(SCREEN_WIDTH // 2, 280))
            self.screen.blit(dungeon_surface, dungeon_rect)
        
        # Player stats
        if self.player:
            level_text = f"Final Level: {self.player.level}"
            level_surface = self.font.render(level_text, True, WHITE)
            level_rect = level_surface.get_rect(center=(SCREEN_WIDTH // 2, 320))
            self.screen.blit(level_surface, level_rect)
        
        # Action buttons
        self.draw_fancy_button(self.screen, SCREEN_WIDTH // 2 - 120, 370, 100, 40, 
                            "R Space", DARK_GREEN, WHITE, LIGHT_GREEN)
        
        self.draw_fancy_button(self.screen, SCREEN_WIDTH // 2 + 20, 370, 100, 40, 
                            "Esc Quit", DARK_GRAY, WHITE, LIGHT_GRAY)
    
    def calculate_manhattan_distance(self, x1, y1, x2, y2): # Counting manhattan distance
        return abs(x1 - x2) + abs(y1 - y2)

    def run(self):
        running = True
        
        while running:
            running = self.handle_events()
            self.update_game()
            
            # Draw based on game state
            if self.game_state == GameState.MAP_VIEW:
                self.draw_map_view()
            elif self.game_state == GameState.DUNGEON:
                self.draw_dungeon_view()
            elif self.game_state == GameState.VICTORY:
                self.draw_victory_screen()
            elif self.game_state == GameState.GAME_OVER:
                self.draw_game_over_screen()
            
            pygame.display.flip()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()
