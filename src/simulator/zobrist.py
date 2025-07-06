"""
Zobrist hashing implementation for GameState.

Provides constant-time hash computation through pre-generated random tables
and incremental XOR updates during game state mutations.
"""

import random
from typing import Dict, Tuple


class ZobristTable:
    """
    Pre-computed Zobrist hash table for game state hashing.
    
    Uses a fixed seed for reproducible hash values across runs.
    """
    
    def __init__(self, seed: int = 12345):
        """Initialize Zobrist table with reproducible random values."""
        random.seed(seed)
        
        # Table for [row][col][rank][suit] combinations
        # Ranks 2-13 (12 values), Suits 0-3 (4 values)
        self.piece_table: Dict[Tuple[int, int, int, int], int] = {}
        
        # Table for gap positions [row][col]
        self.gap_table: Dict[Tuple[int, int], int] = {}
        
        self._generate_tables()
    
    def _generate_tables(self):
        """Generate all Zobrist table entries."""
        # Generate piece table for all valid (row, col, rank, suit) combinations
        for row in range(4):
            for col in range(13):
                for rank in range(2, 14):  # Ranks 2-13 (Aces removed)
                    for suit in range(4):   # Suits 0-3
                        self.piece_table[(row, col, rank, suit)] = random.getrandbits(64)
        
        # Generate gap table for all (row, col) positions
        for row in range(4):
            for col in range(13):
                self.gap_table[(row, col)] = random.getrandbits(64)
    
    def get_piece_hash(self, row: int, col: int, rank: int, suit: int) -> int:
        """Get Zobrist hash for a piece at given position."""
        return self.piece_table[(row, col, rank, suit)]
    
    def get_gap_hash(self, row: int, col: int) -> int:
        """Get Zobrist hash for a gap at given position."""
        return self.gap_table[(row, col)]


# Global Zobrist table instance
_zobrist_table = None


def get_zobrist_table() -> ZobristTable:
    """Get global Zobrist table instance (singleton pattern)."""
    global _zobrist_table
    if _zobrist_table is None:
        _zobrist_table = ZobristTable()
    return _zobrist_table