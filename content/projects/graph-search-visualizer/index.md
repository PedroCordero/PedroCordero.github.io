---
title: Interactive Graph Search Visualizer
summary: A labyrinth game in Python that visualizes how DFS, BFS, greedy lookahead and A* explore a maze in real time.
date: 2025-05-01
cover: ./cover.webp
video: /media/graph-search-visualizer/demo.mp4
tags: [Python, Search algorithms, A*, GUI]
---

A fully interactive, labyrinth-based GUI application in Python that demonstrates and compares classic graph search algorithms. The application simulates a game where a virtual cat must navigate mazes under different goals and constraints using search strategies like DFS, BFS, A\* and heuristic-guided methods.

## Key features

- **Multiple algorithms:** Depth-First Search (DFS), Breadth-First Search (BFS), Lookahead (greedy) and A\* with various heuristics.
- **Interactive GUI:** built with PySimpleGUI. Users can load maps, visualize the search expansion and observe pathfinding decisions in real time.
- **Custom problem settings:** two main scenarios, reaching a goal (the door) and collecting all items (donuts) before exiting.

## Results

- Enabled real-time evaluation of algorithm efficiency across different maze complexities and goal structures.
- Improved understanding of heuristic behavior and algorithm performance trade-offs through direct interaction.
- Showcased the value of interactive learning tools in algorithm education and AI search problems.

<video src="/media/graph-search-visualizer/exit.mp4" autoplay loop muted playsinline></video>

*Problem sample: get to the exit.*

<video src="/media/graph-search-visualizer/donuts.mp4" autoplay loop muted playsinline></video>

*Problem sample: eat all the donuts, then get to the exit.*
