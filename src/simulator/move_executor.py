"""
Move execution module for Gaps Solitaire game states.

This module provides the MoveExecutor class that handles the execution of moves
on GameState objects, maintaining single responsibility - GameState holds data,
MoveExecutor modifies it.
"""

from typing import Tuple, Optional
from .game_state import GameState, CardPosition


class InvalidMoveError(Exception):
    """Exception raised when attempting to execute an invalid move."""
    pass


class MoveExecutor:
    """
    Handles execution of moves on GameState objects.
    
    This class maintains single responsibility by focusing solely on move execution,
    while GameState focuses on data representation and state management.
    """
    
    def execute_move(self, game_state: GameState, move: Tuple[CardPosition, Tuple[int, int]]) -> GameState:
        """
        Execute a move on the game state and return a new GameState.
        
        Args:
            game_state: The current game state
            move: Tuple of (CardPosition, (target_row, target_col))
            
        Returns:
            GameState: New game state with the move applied
            
        Raises:
            InvalidMoveError: If the move is invalid (target occupied, card not found, etc.)
        """
        card, (target_row, target_col) = move
        
        # Validate target position
        if not game_state.is_valid_position(target_row, target_col):
            raise InvalidMoveError(f"Invalid target position: ({target_row}, {target_col})")
            
        # Check if target position is occupied
        if game_state.get_card(target_row, target_col) is not None:
            raise InvalidMoveError(f"Target position ({target_row}, {target_col}) is already occupied")
            
        # Find source position of the card to move
        source_position = self._find_card_position(game_state, card)
        if source_position is None:
            raise InvalidMoveError(f"Card {card} not found on the board")
            
        source_row, source_col = source_position
        
        # Check if source card is in immutable sequence
        if (source_row, source_col) in game_state.immutable_sequences:
            raise InvalidMoveError(f"Cannot move card from immutable sequence at ({source_row}, {source_col})")
            
        # Create a copy of the game state for modification
        new_state = game_state.copy()
        
        # Create gap at source position
        if not new_state.create_gap(source_row, source_col):
            raise InvalidMoveError(f"Failed to create gap at source position ({source_row}, {source_col})")
            
        # Place card at target position
        if not new_state.place_card(card, target_row, target_col):
            raise InvalidMoveError(f"Failed to place card at target position ({target_row}, {target_col})")
            
        # Update immutable sequences after the move
        new_state.detect_immutable_sequences()
        
        return new_state
    
    def _find_card_position(self, game_state: GameState, card: CardPosition) -> Optional[Tuple[int, int]]:
        """
        Find the position of a specific card on the board.
        
        Args:
            game_state: The current game state
            card: The card to find
            
        Returns:
            Tuple[int, int] or None: Position (row, col) if found, None otherwise
        """
        # Scan the board to find the card
        for row in range(4):
            for col in range(13):
                board_card = game_state.get_card(row, col)
                if board_card is not None and board_card.rank == card.rank and board_card.suit == card.suit:
                    return (row, col)
        return None