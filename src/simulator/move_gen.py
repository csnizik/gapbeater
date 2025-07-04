"""
Legal move generation for Gaps Solitaire.

This module generates all legal moves from a given game state,
following the strict rules of Gaps Solitaire as documented in
PROJECT_CONTEXT.md and README.md.

Key Rules:
- Cards can only move into gaps
- Gap must have a card to its left that is exactly one rank lower, same suit
- Cannot move into gaps after Kings (no card higher than King)
- Cannot move into gaps after other gaps
- Cannot move immutable sequence cards
- First column gaps can only be filled with 2s (no left neighbor required)

Performance Requirements:
- Must support 50,000+ position evaluations per second
- Efficient move generation for search algorithms
"""

from typing import List, Set, Tuple, Optional
from dataclasses import dataclass

from .game_state import GameState, Card, Rank, Suit


@dataclass(frozen=True)
class Move:
    """Represents a legal move in Gaps Solitaire."""
    from_row: int
    from_col: int
    to_row: int
    to_col: int
    card: Card
    
    def __str__(self) -> str:
        """String representation of the move."""
        return f"{self.card} from R{self.from_row+1}C{self.from_col+1} to R{self.to_row+1}C{self.to_col+1}"
    
    def to_compact_string(self) -> str:
        """Compact string representation for UI display."""
        return f"{self.card} -> R{self.to_row+1}C{self.to_col+1}"


class MoveGenerator:
    """
    Generates legal moves for Gaps Solitaire positions.
    
    Follows single responsibility principle by focusing solely on move generation
    while maintaining high performance for search algorithms.
    """
    
    def __init__(self, enable_diagnostics: bool = False):
        """Initialize move generator.
        
        Args:
            enable_diagnostics: Enable diagnostic logging
        """
        self.enable_diagnostics = enable_diagnostics
    
    def generate_legal_moves(self, state: GameState) -> List[Move]:
        """
        Generate all legal moves from the current position.
        
        Args:
            state: Current game state
            
        Returns:
            List of all legal moves from this position
        """
        import time
        start_time = time.time()
        
        legal_moves = []
        gaps = state.get_gaps()
        immutable_positions = state.get_immutable_positions()
        
        # Handle first position gaps specially to allow any available 2
        first_position_gaps = [(r, c) for (r, c) in gaps if c == 0]
        other_gaps = [(r, c) for (r, c) in gaps if c != 0]
        
        # For first position gaps, find all available 2s
        if first_position_gaps:
            # Find which suits already have 2s in first column
            occupied_first_column_suits = set()
            for row in range(state.ROWS):
                first_card = state.get_card(row, 0)
                if first_card is not None and first_card.rank.value == 2:  # Rank.TWO
                    occupied_first_column_suits.add(first_card.suit)
            
            # For each first position gap, find the best available 2
            # (preferring one that's not already in a first position)
            for gap_row, gap_col in first_position_gaps:
                best_two = None
                best_position = None
                
                # Look for available 2s (prefer ones not in first column)
                from .game_state import Rank, Suit
                for suit in Suit:
                    if suit in occupied_first_column_suits:
                        continue  # This suit's 2 is already in first column
                    
                    two_card = Card(Rank.TWO, suit)
                    card_pos = self._find_card_position(state, two_card)
                    if card_pos is not None and card_pos[1] != 0:  # Found 2 not in first column
                        # Check if it's movable (not immutable)
                        if card_pos not in immutable_positions:
                            best_two = two_card
                            best_position = card_pos
                            break  # Take the first available one
                
                if best_two and best_position:
                    move = Move(
                        from_row=best_position[0],
                        from_col=best_position[1], 
                        to_row=gap_row,
                        to_col=gap_col,
                        card=best_two
                    )
                    legal_moves.append(move)
        
        # Handle other gaps with normal logic
        for gap_row, gap_col in other_gaps:
            # Find what card can legally fill this gap
            target_card = self._get_required_card_for_gap(state, gap_row, gap_col)
            
            if target_card is None:
                continue  # Gap cannot be filled (after King or another gap)
            
            # Find where this card currently is (if it exists on the board)
            card_position = self._find_card_position(state, target_card)
            
            if card_position is None:
                continue  # Required card not on board
            
            card_row, card_col = card_position
            
            # Check if the card can be moved (not in immutable sequence)
            if (card_row, card_col) in immutable_positions:
                continue  # Cannot move immutable cards
            
            # Valid move found
            move = Move(
                from_row=card_row,
                from_col=card_col,
                to_row=gap_row,
                to_col=gap_col,
                card=target_card
            )
            legal_moves.append(move)
        
        # Diagnostic logging
        if self.enable_diagnostics:
            try:
                from .diagnostics import create_diagnostics, DiagnosticMetrics
                diagnostics = create_diagnostics()
                metrics = DiagnosticMetrics()
                metrics.move_generation_time = time.time() - start_time
                diagnostics.log_move_generation(state, legal_moves, metrics)
                diagnostics.log_edge_case_handling(state, self)
            except ImportError:
                pass  # Diagnostics not available
        
        return legal_moves
    
    def _get_required_card_for_gap(self, state: GameState, gap_row: int, gap_col: int) -> Optional[Card]:
        """
        Determine what card can legally fill a specific gap.
        
        Args:
            state: Current game state
            gap_row: Row of the gap
            gap_col: Column of the gap
            
        Returns:
            Card that can fill the gap, or None if gap cannot be filled
        """
        if gap_col == 0:
            # First column gaps can only be filled with 2s that are not already in first positions
            # Check which 2s are available (not already in first column)
            occupied_first_column_suits = set()
            for row in range(state.ROWS):
                first_card = state.get_card(row, 0)
                if first_card is not None and first_card.rank == Rank.TWO:
                    occupied_first_column_suits.add(first_card.suit)
            
            # Find available 2s not in first column
            for suit in Suit:
                if suit in occupied_first_column_suits:
                    continue  # This suit's 2 is already in first column
                
                two_card = Card(Rank.TWO, suit)
                card_pos = self._find_card_position(state, two_card)
                if card_pos is not None and card_pos[1] != 0:  # Found 2 not in first column
                    return two_card
            return None
        
        # For other columns, check the card to the left
        left_card = state.get_card(gap_row, gap_col - 1)
        
        if left_card is None:
            # Gap to the left - cannot fill this gap
            return None
        
        if left_card.rank == Rank.KING:
            # Cannot place anything after a King
            return None
        
        # Next card in sequence
        next_rank_value = left_card.rank.value + 1
        try:
            next_rank = Rank(next_rank_value)
            return Card(next_rank, left_card.suit)
        except ValueError:
            # Rank beyond King
            return None
    
    def _find_card_position(self, state: GameState, target_card: Card) -> Optional[Tuple[int, int]]:
        """
        Find the current position of a specific card on the board.
        
        Args:
            state: Current game state
            target_card: Card to find
            
        Returns:
            (row, col) position of the card, or None if not found
        """
        for row in range(state.ROWS):
            for col in range(state.COLS):
                card = state.get_card(row, col)
                if card == target_card:
                    return (row, col)
        return None
    
    def is_legal_move(self, state: GameState, move: Move) -> bool:
        """
        Check if a specific move is legal in the current position.
        
        Args:
            state: Current game state
            move: Move to validate
            
        Returns:
            True if move is legal, False otherwise
        """
        # Check if source position has the expected card
        source_card = state.get_card(move.from_row, move.from_col)
        if source_card != move.card:
            return False
        
        # Check if destination is a gap
        dest_card = state.get_card(move.to_row, move.to_col)
        if dest_card is not None:
            return False
        
        # Check if source card is immutable
        immutable_positions = state.get_immutable_positions()
        if (move.from_row, move.from_col) in immutable_positions:
            return False
        
        # Check if destination gap can accept this card
        required_card = self._get_required_card_for_gap(state, move.to_row, move.to_col)
        return required_card == move.card
    
    def apply_move(self, state: GameState, move: Move) -> GameState:
        """
        Apply a move to a game state, returning a new state.
        
        Args:
            state: Current game state
            move: Move to apply
            
        Returns:
            New game state with move applied
            
        Raises:
            ValueError: If move is not legal
        """
        if not self.is_legal_move(state, move):
            raise ValueError(f"Illegal move: {move}")
        
        # Create new state
        new_state = state.copy()
        
        # Remove card from source position
        new_state.set_card(move.from_row, move.from_col, None)
        
        # Place card at destination
        new_state.set_card(move.to_row, move.to_col, move.card)
        
        return new_state
    
    def get_move_count(self, state: GameState) -> int:
        """
        Get the number of legal moves from current position.
        
        This is more efficient than generating all moves when you only need the count.
        
        Args:
            state: Current game state
            
        Returns:
            Number of legal moves available
        """
        count = 0
        gaps = state.get_gaps()
        immutable_positions = state.get_immutable_positions()
        
        for gap_row, gap_col in gaps:
            target_card = self._get_required_card_for_gap(state, gap_row, gap_col)
            if target_card is None:
                continue
            
            card_position = self._find_card_position(state, target_card)
            if card_position is None:
                continue
            
            if card_position in immutable_positions:
                continue
            
            count += 1
        
        return count


def create_move_generator(enable_diagnostics: bool = False) -> MoveGenerator:
    """
    Factory function to create a MoveGenerator instance.
    
    This follows the dependency injection principle for better testability
    and future extensibility.
    
    Args:
        enable_diagnostics: Enable diagnostic logging
    
    Returns:
        Configured MoveGenerator instance
    """
    return MoveGenerator(enable_diagnostics=enable_diagnostics)