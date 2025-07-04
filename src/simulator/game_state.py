"""
Efficient game state representation for Gaps Solitaire.

This module provides optimized board representation and state management
following the performance targets and architectural principles outlined
in PROJECT_CONTEXT.md.

Key Requirements:
- Efficient memory usage (<100MB for complete analysis)
- Fast position evaluation (50,000+ positions/second)
- Support for Zobrist hashing for transposition tables
- Immutable sequence tracking for reshuffle mechanics
"""

from typing import List, Set, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class Suit(Enum):
    """Card suits enumeration."""
    CLUBS = 'C'
    DIAMONDS = 'D'
    HEARTS = 'H'
    SPADES = 'S'


class Rank(Enum):
    """Card ranks enumeration (Aces removed for Gaps Solitaire)."""
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13


@dataclass(frozen=True)
class Card:
    """Immutable card representation."""
    rank: Rank
    suit: Suit
    
    def __str__(self) -> str:
        rank_str = 'X' if self.rank == Rank.TEN else str(self.rank.value)[0]
        if self.rank in [Rank.JACK, Rank.QUEEN, Rank.KING]:
            rank_str = self.rank.name[0]
        return f"{rank_str}{self.suit.value}"
    
    @classmethod
    def from_string(cls, card_str: str) -> 'Card':
        """Create card from string representation (e.g., '4C', 'XD')."""
        if len(card_str) != 2:
            raise ValueError(f"Invalid card string: {card_str}")
        
        rank_str, suit_str = card_str[0].upper(), card_str[1].upper()
        
        # Parse rank
        if rank_str == 'X':
            rank = Rank.TEN
        elif rank_str == 'J':
            rank = Rank.JACK
        elif rank_str == 'Q':
            rank = Rank.QUEEN
        elif rank_str == 'K':
            rank = Rank.KING
        else:
            try:
                rank_val = int(rank_str)
                rank = Rank(rank_val)
            except (ValueError, KeyError):
                raise ValueError(f"Invalid rank: {rank_str}")
        
        # Parse suit
        try:
            suit = Suit(suit_str)
        except ValueError:
            raise ValueError(f"Invalid suit: {suit_str}")
        
        return cls(rank=rank, suit=suit)


class GameState:
    """
    Efficient game state representation for Gaps Solitaire.
    
    Maintains board state, tracks immutable sequences, and provides
    efficient operations for search algorithms.
    """
    
    ROWS = 4
    COLS = 13
    TOTAL_POSITIONS = ROWS * COLS
    
    def __init__(self, board: Optional[List[Optional[Card]]] = None):
        """
        Initialize game state.
        
        Args:
            board: List of 52 positions (4 rows × 13 cols), None represents gaps
        """
        if board is None:
            self.board: List[Optional[Card]] = [None] * self.TOTAL_POSITIONS
        else:
            if len(board) != self.TOTAL_POSITIONS:
                raise ValueError(f"Board must have exactly {self.TOTAL_POSITIONS} positions")
            self.board = board.copy()
        
        self._immutable_positions: Set[int] = set()
        self._gap_positions: Set[int] = set()
        self._zobrist_hash: Optional[int] = None
        self._update_derived_state()
    
    def _update_derived_state(self) -> None:
        """Update gap positions and immutable sequences."""
        self._gap_positions.clear()
        self._immutable_positions.clear()
        
        # Find gaps
        for i, card in enumerate(self.board):
            if card is None:
                self._gap_positions.add(i)
        
        # Find immutable sequences (starting with 2, same suit, consecutive)
        for row in range(self.ROWS):
            start_pos = row * self.COLS
            sequence_positions = []
            
            for col in range(self.COLS):
                pos = start_pos + col
                card = self.board[pos]
                
                if card is None:
                    break  # Gap breaks sequence
                
                if col == 0:
                    # First position must be a 2 to start immutable sequence
                    if card.rank == Rank.TWO:
                        sequence_positions.append(pos)
                    else:
                        break
                else:
                    # Check if continues sequence
                    prev_card = self.board[sequence_positions[-1]]
                    if (card.rank.value == prev_card.rank.value + 1 and 
                        card.suit == prev_card.suit):
                        sequence_positions.append(pos)
                    else:
                        break
            
            # Mark sequence as immutable
            self._immutable_positions.update(sequence_positions)
        
        # Reset hash when state changes
        self._zobrist_hash = None
    
    def get_card(self, row: int, col: int) -> Optional[Card]:
        """Get card at specific position."""
        if not (0 <= row < self.ROWS and 0 <= col < self.COLS):
            raise ValueError(f"Invalid position: row={row}, col={col}")
        return self.board[row * self.COLS + col]
    
    def set_card(self, row: int, col: int, card: Optional[Card]) -> None:
        """Set card at specific position."""
        if not (0 <= row < self.ROWS and 0 <= col < self.COLS):
            raise ValueError(f"Invalid position: row={row}, col={col}")
        
        pos = row * self.COLS + col
        if pos in self._immutable_positions:
            raise ValueError(f"Cannot modify immutable position: row={row}, col={col}")
        
        self.board[pos] = card
        self._update_derived_state()
    
    def get_gaps(self) -> Set[Tuple[int, int]]:
        """Get all gap positions as (row, col) tuples."""
        return {(pos // self.COLS, pos % self.COLS) for pos in self._gap_positions}
    
    def get_immutable_positions(self) -> Set[Tuple[int, int]]:
        """Get all immutable positions as (row, col) tuples."""
        return {(pos // self.COLS, pos % self.COLS) for pos in self._immutable_positions}
    
    def is_winning_position(self) -> bool:
        """Check if current state is a winning position."""
        for row in range(self.ROWS):
            for col in range(self.COLS - 1):  # Last column should be gap
                card = self.get_card(row, col)
                if card is None:
                    return False
                expected_rank = Rank(col + 2)  # 2, 3, 4, ..., K
                if card.rank != expected_rank:
                    return False
            
            # Last column should be gap
            if self.get_card(row, self.COLS - 1) is not None:
                return False
        
        return True
    
    def copy(self) -> 'GameState':
        """Create a deep copy of the game state."""
        return GameState(self.board)
    
    def get_zobrist_hash(self) -> int:
        """Get Zobrist hash for transposition table lookup."""
        # TODO: Implement Zobrist hashing for efficient position caching
        # This is a stub implementation
        if self._zobrist_hash is None:
            self._zobrist_hash = hash(tuple(str(card) if card else '--' for card in self.board))
        return self._zobrist_hash
    
    def __str__(self) -> str:
        """String representation of the board."""
        lines = []
        for row in range(self.ROWS):
            row_cards = []
            for col in range(self.COLS):
                card = self.get_card(row, col)
                row_cards.append(str(card) if card else '--')
            lines.append(' | '.join(row_cards))
        return '\n'.join(lines)
    
    def __eq__(self, other) -> bool:
        """Equality comparison for game states."""
        if not isinstance(other, GameState):
            return False
        return self.board == other.board
    
    def __hash__(self) -> int:
        """Hash for use in sets and dictionaries."""
        return self.get_zobrist_hash()


def create_initial_state(card_strings: List[str]) -> GameState:
    """
    Create initial game state from list of card strings.
    
    Args:
        card_strings: List of 52 card strings (e.g., ['4C', '--', 'XD', ...])
                     Use '--' for gaps
    
    Returns:
        GameState initialized with the given cards
    """
    if len(card_strings) != GameState.TOTAL_POSITIONS:
        raise ValueError(f"Must provide exactly {GameState.TOTAL_POSITIONS} card strings")
    
    board = []
    for card_str in card_strings:
        if card_str == '--' or card_str is None:
            board.append(None)
        else:
            board.append(Card.from_string(card_str))
    
    return GameState(board)