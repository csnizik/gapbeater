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
# TARGET_SPEED, RESPONSE_TIME_LIMIT, and MEMORY_LIMIT have been removed
# as they are not actually used in the search behavior

# Optimization technique toggles
ALPHA_BETA_PRUNING = True  # Range: true/false | Default true | Enable alpha-beta pruning optimization
TRANSPOSITION_TABLES = True  # Range: true/false | Default true | Enable transposition table caching
ITERATIVE_DEEPENING = True  # Range: true/false | Default true | Enable iterative deepening search
MOVE_ORDERING = True  # Range: true/false | Default true | Enable intelligent move ordering

# Move evaluation constants
SEQUENCE_PREFERENCE_MULTIPLIER = 1.5  # Range: 1.0-3.0 | Default 1.5 | Preference multiplier for sequence-building moves over gap-creating moves

# Diagnostic options
ENABLE_DIAGNOSTICS = False  # Range: true/false | Default false | Enable detailed diagnostic logging
PERFORMANCE_TRACKING = False  # Range: true/false | Default false | Enable performance metrics tracking
