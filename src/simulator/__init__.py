"""
Simulator package for GapBeater - Advanced search and optimization components.

This package implements the core algorithmic components for Gaps Solitaire optimization,
following chess engine techniques adapted for single-player solitaire.

Components:
- game_state.py: Efficient board representation and state management
- move_gen.py: Legal move generation following game rules
- evaluator.py: Position evaluation and multi-factor scoring
- search.py: Tree search algorithms (minimax, alpha-beta, iterative deepening)
- optimizer.py: Multi-phase strategic planning and analysis

All components must adhere to SOLID principles and performance targets:
- 50,000+ positions evaluated per second
- <2 second response times
- <100MB memory usage for complete analysis
"""