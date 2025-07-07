"""
Position evaluation system for Gaps Solitaire.

This module provides strategic evaluation of game positions, scoring based on
correctly placed cards and gap quality for search algorithms.
"""

from typing import TYPE_CHECKING
import time
import logging
from pathlib import Path

if TYPE_CHECKING:
    from .game_state import GameState


class PositionEvaluatorDiagnostics:
    """Diagnostic logging for position evaluation operations"""
    
    def __init__(self, log_file_path: str = None):
        # Check if we should use timestamped directory
        if log_file_path is None:
            from ..config.settings_manager import SettingsManager
            settings_manager = SettingsManager()
            current_log_dir = settings_manager.get_current_log_directory()
            if current_log_dir:
                log_file_path = str(current_log_dir / "position_evaluator_diagnostics.log")
            else:
                log_file_path = "debug/position_evaluator_diagnostics.log"
        
        self.log_file_path = Path(log_file_path)
        self.log_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Configure logging
        self.logger = logging.getLogger("PositionEvaluatorDiagnostics")
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
        self.evaluation_times = []
        self.evaluation_count = 0
        self.score_history = []
    
    def log_evaluation(self, score: float, evaluation_time: float, correctly_placed: int, dead_gaps: int):
        """Log position evaluation details"""
        self.logger.info(f"Position evaluation: score={score:.2f}, time={evaluation_time:.4f}s")
        self.logger.debug(f"Correctly placed cards: {correctly_placed}, dead gaps: {dead_gaps}")
        
        self.evaluation_times.append(evaluation_time)
        self.score_history.append(score)
        self.evaluation_count += 1
    
    def log_performance_summary(self):
        """Log aggregate performance metrics"""
        if not self.evaluation_times:
            return
            
        avg_time = sum(self.evaluation_times) / len(self.evaluation_times)
        max_time = max(self.evaluation_times)
        min_time = min(self.evaluation_times)
        avg_score = sum(self.score_history) / len(self.score_history)
        
        self.logger.info("=== Position Evaluation Performance Summary ===")
        self.logger.info(f"Total evaluations: {self.evaluation_count}")
        self.logger.info(f"Average evaluation time: {avg_time:.6f}s")
        self.logger.info(f"Max evaluation time: {max_time:.6f}s")
        self.logger.info(f"Min evaluation time: {min_time:.6f}s")
        self.logger.info(f"Average score: {avg_score:.2f}")


class PositionEvaluator:
    """
    Strategic position evaluator for Gaps Solitaire game states.
    
    Follows single responsibility principle by focusing solely on position evaluation.
    Reuses GameState's immutable_sequences for efficient scoring.
    """

    # Evaluation weights for scoring components
    CORRECT_PLACEMENT_WEIGHT = 50.0  # Heavy weight for correctly placed cards
    DEAD_GAP_PENALTY = -5.0          # Penalty for gaps after Kings
    BASE_SCORE = 50.0                # Base score for normalization

    def __init__(self, enable_performance_tracking: bool = True, enable_diagnostics: bool = False):
        """Initialize position evaluator with optional performance tracking and diagnostics."""
        self.enable_performance_tracking = enable_performance_tracking
        self.evaluation_count = 0
        self.total_evaluation_time = 0.0
        self.diagnostics = PositionEvaluatorDiagnostics() if enable_diagnostics else None
        
        # Pre-calculate constants for performance
        self._max_possible_score = self.BASE_SCORE + (52 * self.CORRECT_PLACEMENT_WEIGHT)
        self._normalization_factor = 100.0 / self._max_possible_score

    def evaluate(self, game_state: 'GameState') -> float:
        """
        Evaluate game position and return normalized score (0-100 range).

        Args:
            game_state: GameState to evaluate

        Returns:
            float: Normalized score where higher values indicate better positions
        """
        if self.enable_performance_tracking or self.diagnostics:
            start_time = time.perf_counter()
        
        # Score correctly placed cards using existing immutable_sequences
        correct_placements = len(game_state.immutable_sequences)
        correct_placement_score = correct_placements * self.CORRECT_PLACEMENT_WEIGHT

        # Penalize dead gaps (gaps after Kings) - optimized version
        dead_gaps = self._count_dead_gaps_optimized(game_state)
        dead_gap_penalty = dead_gaps * self.DEAD_GAP_PENALTY

        # Calculate raw score using weighted sum
        raw_score = self.BASE_SCORE + correct_placement_score + dead_gap_penalty

        # Normalize to 0-100 range using pre-calculated constants
        normalized_score = raw_score * self._normalization_factor
        
        # Clamp to valid range (faster than max/min with constants)
        if normalized_score < 0.0:
            normalized_score = 0.0
        elif normalized_score > 100.0:
            normalized_score = 100.0

        # Track performance metrics and log diagnostics
        if self.enable_performance_tracking or self.diagnostics:
            evaluation_time = time.perf_counter() - start_time
            
        if self.enable_performance_tracking:
            self.evaluation_count += 1
            self.total_evaluation_time += evaluation_time

        if self.diagnostics:
            self.diagnostics.log_evaluation(normalized_score, evaluation_time, correct_placements, dead_gaps)

        return normalized_score

    def _count_dead_gaps_optimized(self, game_state: 'GameState') -> int:
        """
        Optimized version of dead gap counting that avoids validation overhead.
        
        Count gaps that appear immediately after Kings (dead gaps).
        Dead gaps cannot be filled because no card ranks higher than King.
        
        Args:
            game_state: GameState to analyze
            
        Returns:
            int: Number of dead gaps found
        """
        dead_gap_count = 0
        board = game_state.board  # Cache board reference
        
        for gap_row, gap_col in game_state.gaps:
            # Check if gap is immediately after a King
            if gap_col > 0:  # Not in first column
                # Direct board access instead of get_card to avoid validation overhead
                card_to_left = board[gap_row][gap_col - 1]
                if card_to_left is not None and card_to_left.rank == 13:  # King = rank 13
                    dead_gap_count += 1
                    
        return dead_gap_count

    def _count_dead_gaps(self, game_state: 'GameState') -> int:
        """
        Count gaps that appear immediately after Kings (dead gaps).
        
        Dead gaps cannot be filled because no card ranks higher than King.
        
        Args:
            game_state: GameState to analyze
            
        Returns:
            int: Number of dead gaps found
        """
        dead_gap_count = 0
        
        for gap_row, gap_col in game_state.gaps:
            # Check if gap is immediately after a King
            if gap_col > 0:  # Not in first column
                card_to_left = game_state.get_card(gap_row, gap_col - 1)
                if card_to_left and card_to_left.rank == 13:  # King = rank 13
                    dead_gap_count += 1
                    
        return dead_gap_count

    def get_performance_stats(self) -> dict:
        """
        Get performance statistics for evaluation function.
        
        Returns:
            dict: Performance metrics including evaluation count and timing
        """
        if self.evaluation_count == 0:
            avg_time = 0.0
        else:
            avg_time = self.total_evaluation_time / self.evaluation_count
            
        return {
            'evaluation_count': self.evaluation_count,
            'total_time': self.total_evaluation_time,
            'average_time': avg_time,
            'evaluations_per_second': 1.0 / avg_time if avg_time > 0 else 0
        }