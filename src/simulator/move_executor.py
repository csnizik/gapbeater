"""
Move execution module for Gaps Solitaire game states.

This module provides the MoveExecutor class that handles the execution of moves
on GameState objects, maintaining single responsibility - GameState holds data,
MoveExecutor modifies it.
"""

from typing import Tuple, Optional
import time
import logging
from pathlib import Path
from .game_state import GameState, CardPosition


class InvalidMoveError(Exception):
    """Exception raised when attempting to execute an invalid move."""
    pass


class MoveExecutorDiagnostics:
    """Diagnostic logging for move execution operations"""
    
    def __init__(self, log_file_path: str = None):
        # Check if we should use timestamped directory
        if log_file_path is None:
            from ..config.settings_manager import SettingsManager
            settings_manager = SettingsManager()
            current_log_dir = settings_manager.get_current_log_directory()
            if current_log_dir:
                log_file_path = str(current_log_dir / "move_executor_diagnostics.log")
            else:
                log_file_path = "debug/move_executor_diagnostics.log"
        
        self.log_file_path = Path(log_file_path)
        self.log_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Configure logging
        self.logger = logging.getLogger("MoveExecutorDiagnostics")
        self.logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers to avoid duplicates
        self.logger.handlers.clear()
        
        # File handler
        file_handler = logging.FileHandler(self.log_file_path, mode='w')
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # Performance tracking
        self.move_execution_times = []
        self.moves_executed = 0
    
    def log_move_execution(self, move: Tuple[CardPosition, Tuple[int, int]], execution_time: float, success: bool):
        """Log move execution details"""
        card, (target_row, target_col) = move
        card_str = f"{card.rank}{card.suit}"
        
        if success:
            self.logger.info(f"Move executed: {card_str} -> ({target_row}, {target_col}) in {execution_time:.4f}s")
        else:
            self.logger.error(f"Move failed: {card_str} -> ({target_row}, {target_col})")
        
        if success:
            self.move_execution_times.append(execution_time)
            self.moves_executed += 1
    
    def log_invalid_move(self, move: Tuple[CardPosition, Tuple[int, int]], error_msg: str):
        """Log invalid move attempts"""
        card, (target_row, target_col) = move
        card_str = f"{card.rank}{card.suit}"
        self.logger.warning(f"Invalid move: {card_str} -> ({target_row}, {target_col}) - {error_msg}")
    
    def log_performance_summary(self):
        """Log aggregate performance metrics"""
        if not self.move_execution_times:
            return
            
        avg_time = sum(self.move_execution_times) / len(self.move_execution_times)
        max_time = max(self.move_execution_times)
        min_time = min(self.move_execution_times)
        
        self.logger.info("=== Move Execution Performance Summary ===")
        self.logger.info(f"Total moves executed: {self.moves_executed}")
        self.logger.info(f"Average execution time: {avg_time:.6f}s")
        self.logger.info(f"Max execution time: {max_time:.6f}s")
        self.logger.info(f"Min execution time: {min_time:.6f}s")


class MoveExecutor:
    """
    Handles execution of moves on GameState objects.
    
    This class maintains single responsibility by focusing solely on move execution,
    while GameState focuses on data representation and state management.
    """
    
    def __init__(self, enable_diagnostics: bool = False):
        """Initialize MoveExecutor with optional diagnostics."""
        self.diagnostics = MoveExecutorDiagnostics() if enable_diagnostics else None
    
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
        
        if self.diagnostics:
            start_time = time.perf_counter()
        
        try:
            # Validate target position
            if not game_state.is_valid_position(target_row, target_col):
                error_msg = f"Invalid target position: ({target_row}, {target_col})"
                if self.diagnostics:
                    self.diagnostics.log_invalid_move(move, error_msg)
                raise InvalidMoveError(error_msg)
                
            # Check if target position is occupied
            if game_state.get_card(target_row, target_col) is not None:
                error_msg = f"Target position ({target_row}, {target_col}) is already occupied"
                if self.diagnostics:
                    self.diagnostics.log_invalid_move(move, error_msg)
                raise InvalidMoveError(error_msg)
                
            # Find source position of the card to move
            source_position = self._find_card_position(game_state, card)
            if source_position is None:
                error_msg = f"Card {card} not found on the board"
                if self.diagnostics:
                    self.diagnostics.log_invalid_move(move, error_msg)
                raise InvalidMoveError(error_msg)
                
            source_row, source_col = source_position
            
            # Check if source card is in immutable sequence
            if (source_row, source_col) in game_state.immutable_sequences:
                error_msg = f"Cannot move card from immutable sequence at ({source_row}, {source_col})"
                if self.diagnostics:
                    self.diagnostics.log_invalid_move(move, error_msg)
                raise InvalidMoveError(error_msg)
                
            # Create a copy of the game state for modification
            new_state = game_state.copy()
            
            # Create gap at source position
            if not new_state.create_gap(source_row, source_col):
                error_msg = f"Failed to create gap at source position ({source_row}, {source_col})"
                if self.diagnostics:
                    self.diagnostics.log_invalid_move(move, error_msg)
                raise InvalidMoveError(error_msg)
                
            # Place card at target position
            if not new_state.place_card(card, target_row, target_col):
                error_msg = f"Failed to place card at target position ({target_row}, {target_col})"
                if self.diagnostics:
                    self.diagnostics.log_invalid_move(move, error_msg)
                raise InvalidMoveError(error_msg)
                
            # Update immutable sequences after the move
            new_state.detect_immutable_sequences()
            
            # Log successful execution
            if self.diagnostics:
                execution_time = time.perf_counter() - start_time
                self.diagnostics.log_move_execution(move, execution_time, True)
            
            return new_state
            
        except InvalidMoveError:
            # Log failed execution
            if self.diagnostics:
                execution_time = time.perf_counter() - start_time
                self.diagnostics.log_move_execution(move, execution_time, False)
            raise
    
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