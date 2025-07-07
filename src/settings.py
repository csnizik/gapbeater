"""
Performance settings constants for GapBeater application.

This module contains all configurable performance parameters as constants
with their valid ranges and descriptions.
"""

# Search algorithm settings
SEARCH_DEPTH = 15  # Range: 1-25 | Default 15 | Maximum depth for minimax search algorithm
SEARCH_TIME_LIMIT = 6.0  # Range: 0.1-30.0 | Default 6.0 | Maximum time for iterative deepening search (seconds)
MAX_ITERATIONS = 104  # Range: 1-1000 | Default 100 | Maximum iterations for search algorithms

# Performance target settings
TARGET_SPEED = 50000  # Range: 1000-1000000 | Default 50000 | Target positions evaluated per second
RESPONSE_TIME_LIMIT = 2.0  # Range: 0.1-10.0 | Default 2.0 | Maximum acceptable response time (seconds)
MEMORY_LIMIT = 100  # Range: 10-1000 | Default 100 | Maximum memory usage (MB)

# Optimization technique toggles
ALPHA_BETA_PRUNING = True  # Range: true/false | Default true | Enable alpha-beta pruning optimization
TRANSPOSITION_TABLES = True  # Range: true/false | Default true | Enable transposition table caching
ITERATIVE_DEEPENING = True  # Range: true/false | Default true | Enable iterative deepening search
MOVE_ORDERING = True  # Range: true/false | Default true | Enable intelligent move ordering

# Evaluator weight constants
GAP_CREATION_WEIGHT = 100.0  # Range: 0.0-1000.0 | Default 100.0 | Weight for gap creation in position evaluation
SEQUENCE_WEIGHT = 200.0  # Range: 0.0-1000.0 | Default 200.0 | Weight for sequence building in evaluation

# Diagnostic options
ENABLE_DIAGNOSTICS = False  # Range: true/false | Default false | Enable detailed diagnostic logging
PERFORMANCE_TRACKING = False  # Range: true/false | Default false | Enable performance metrics tracking
