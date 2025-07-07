"""
Global constants for the GapBeater application.
"""

# --- Board & Deck Configuration ---
BOARD_ROWS = 4
BOARD_COLS = 13
DECK_SIZE = BOARD_ROWS * BOARD_COLS

# --- Card Ranks & Suits ---
# Using 'X' for 10 to keep card strings at 2 chars
VALID_RANKS = {'2', '3', '4', '5', '6', '7', '8', '9', 'X', 'J', 'Q', 'K', 'A'}
VALID_SUITS = {'S', 'H', 'D', 'C'}

RANK_MAP = {2: '2', 3: '3', 4: '4', 5: '5', 6: '6', 7: '7', 8: '8', 9: '9', 10: 'X', 11: 'J', 12: 'Q', 13: 'K'}
SUIT_MAP = {0: 'C', 1: 'D', 2: 'H', 3: 'S'}

# Reverse for lookup
REVERSE_RANK_MAP = { v: k for k, v in RANK_MAP.items()}
REVERSE_SUIT_MAP = { v: k for k, v in SUIT_MAP.items()}

# --- File System ---
SAVES_DIR = "saves"

# --- User Input ---
EXIT_KEY = 'z'
EMPTY_CELL_STR = "--"

# --- Search Configuration ---
# Import performance settings from centralized settings module
from src.settings import SEARCH_DEPTH as DEFAULT_SEARCH_DEPTH
from src.settings import SEARCH_TIME_LIMIT as MAX_SEARCH_TIME_SECONDS
from src.settings import MAX_ITERATIONS
