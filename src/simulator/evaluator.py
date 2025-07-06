"""
Position evaluation system for Gaps Solitaire.

This module provides strategic evaluation of game positions, scoring based on
correctly placed cards and gap quality for search algorithms.
"""

from typing import TYPE_CHECKING
import time

if TYPE_CHECKING:
    from .game_state import GameState


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

    def __init__(self):
        """Initialize position evaluator with performance tracking."""
        self.evaluation_count = 0
        self.total_evaluation_time = 0.0

    def evaluate(self, game_state: 'GameState') -> float:
        """
        Evaluate game position and return normalized score (0-100 range).

        Args:
            game_state: GameState to evaluate

        Returns:
            float: Normalized score where higher values indicate better positions
        """
        start_time = time.perf_counter()
        
        # Score correctly placed cards using existing immutable_sequences
        correct_placements = len(game_state.immutable_sequences)
        correct_placement_score = correct_placements * self.CORRECT_PLACEMENT_WEIGHT

        # Penalize dead gaps (gaps after Kings)
        dead_gaps = self._count_dead_gaps(game_state)
        dead_gap_penalty = dead_gaps * self.DEAD_GAP_PENALTY

        # Calculate raw score using weighted sum
        raw_score = self.BASE_SCORE + correct_placement_score + dead_gap_penalty

        # Normalize to 0-100 range
        # Maximum possible score: BASE_SCORE + (52 * CORRECT_PLACEMENT_WEIGHT)
        # Minimum practical score: 0 (never goes below due to base score and clamping)
        max_possible_score = self.BASE_SCORE + (52 * self.CORRECT_PLACEMENT_WEIGHT)
        normalized_score = max(0.0, min(100.0, (raw_score / max_possible_score) * 100.0))

        # Track performance metrics
        evaluation_time = time.perf_counter() - start_time
        self.evaluation_count += 1
        self.total_evaluation_time += evaluation_time

        return normalized_score

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