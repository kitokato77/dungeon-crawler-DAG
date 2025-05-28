# 🧙‍♂️ Dungeon Crawler - DAG Level System with A* Pathfinding

Welcome to **Dungeon Crawler**, a 2D pixel-art game built with **Python and Pygame**, featuring procedurally generated dungeons, enemy AI using **A\*** pathfinding, and a **DAG (Directed Acyclic Graph)** level system for non-linear progression.

---

## 🎮 Game Overview

In this game, you take on the role of a brave adventurer, clearing out a series of increasingly challenging dungeons. Progress through a world map represented by a **DAG**, where each dungeon unlocks based on its dependencies. Fight off enemies, collect treasures, and conquer the final boss to win the game!

---

## 🧩 Features

- ✅ **Directed Acyclic Graph (DAG)** based level system
- ✅ **Procedural dungeon generation**
- ✅ **A\* Pathfinding Algorithm** for enemy movement
- ✅ Melee and ranged enemies with patrol and attack behaviors
- ✅ Treasure collection, healing, and experience-based leveling
- ✅ Projectiles (player & enemy)
- ✅ Background music and sound effects
- ✅ Fancy UI and visual feedback (health bars, highlights, etc.)

---

## 🚀 Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/kitokato77/dungeon-crawler-DAG.git
   cd dungeon-crawler
   ```

2. Install dependencies (requires Python ≥ 3.8):

   ```bash
   pip install pygame
   ```

3. Run the game:

   ```bash
   python main.py
   ```

---

## 🎹 Sound & Music

Place all audio files in the `assets/` folder:

| File Name         | Description                       |
| ----------------- | --------------------------------- |
| `map.mp3`         | Background music for map view     |
| `battle.mp3`      | Music played in dungeon battles   |
| `buttonclick.wav` | Played on any key or button press |
| `playeratt.wav`   | Player shooting a projectile      |
| `enemiesatt.wav`  | Enemy launching a projectile      |
| `collecttre.wav`  | Collecting a treasure             |

Make sure all files are in `.mp3` or `.wav` format (no `.mp4a`).

---

## 🎮 Controls

| Action         | Key                         |
| -------------- | --------------------------- |
| Move           | Arrow keys (↑ ↓ ← →)        |
| Shoot          | Space + direction           |
| Return to map  | Escape                      |
| Interact (Map) | Click on available dungeons |
| Regenerate map | R                           |

---

## 🧠 Algorithms Used

* **A\* Pathfinding** for enemy navigation
* **Breadth-First Search (BFS)** for unlocking nodes in the DAG
* **Manhattan Distance Heuristic** for A\*
* **Random generation** for procedural dungeon layout

---

## 📁 Project Structure

```
├── main.py                # Entry point
├── game.py                # Main game loop and logic
├── entities.py            # Player, enemy, and projectile behavior
├── dungeon.py             # Dungeon generation and layout
├── dag_manager.py         # DAG node handling and logic
├── constants.py           # Colors, screen size, enums
├── assets/                # Sound, music, fonts
└── README.md              # You are here!
```

---

## 🧑‍💻 Credits

* Developed by: Mochammad Irham Maulana
* Sound effects from: [pixabay.com](https://pixabay.com/music/search/dnd/)
* Inspired by classic roguelike games and strategy pathfinding mechanics

---

## 📜 License

This project is open source and free to use under the [MIT License](LICENSE).

---

Enjoy the adventure, and feel free to contribute or fork this project for your own dungeon game ideas!
