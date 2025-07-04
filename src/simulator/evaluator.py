"""
Position evaluation system for Gaps Solitaire.

This module provides multi-factor position evaluation following the strategic
principles outlined in PROJECT_CONTEXT.md. The evaluator considers immediate
tactical goals and long-term strategic positioning.

Key Evaluation Factors:
1. Sequence Progress: Reward correctly placed sequences
2. Gap Positioning: Favor gaps that enable sequence building
3. King Trap Avoidance: Penalize gaps after Kings
4. Row Balance: Maintain even progress across rows
5. Reshuffle Potential: Consider cards available for reshuffles

Performance Requirements:
- Must support 50,000+ position evaluations per second
- Efficient evaluation for deep search algorithms
"""

from typing import Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum

from .game_state import GameState, Card, Rank, Suit


class EvaluationFeature(Enum):
    """Different factors in position evaluation."""
    SEQUENCE_PROGRESS = "sequence_progress"
    GAP_QUALITY = "gap_quality"
    KING_TRAP_PENALTY = "king_trap_penalty"
    ROW_BALANCE = "row_balance"
    RESHUFFLE_POTENTIAL = "reshuffle_potential"
    MOVE_AVAILABILITY = "move_availability"


@dataclass
class EvaluationResult:
    """Result of position evaluation with detailed breakdown."""
    total_score: float
    feature_scores: Dict[EvaluationFeature, float]
    is_winning: bool
    is_terminal: bool
    
    def __str__(self) -> str:
        """String representation of evaluation result."""
        lines = [f"Total Score: {self.total_score:.2f}"]
        if self.is_winning:
            lines.append("WINNING POSITION")
        if self.is_terminal:
            lines.append("TERMINAL POSITION")
        
        lines.append("Feature Breakdown:")
        for feature, score in self.feature_scores.items():
            lines.append(f"  {feature.value}: {score:.2f}")
        
        return "\n".join(lines)


class PositionEvaluator:
    """
    Multi-factor position evaluator for Gaps Solitaire.
    
    Implements strategic evaluation considering both immediate tactical
    gains and long-term strategic positioning, following the principles
    documented in PROJECT_CONTEXT.md.
    """
    
    # Evaluation weights for different factors
    DEFAULT_WEIGHTS = {
        EvaluationFeature.SEQUENCE_PROGRESS: 100.0,
        EvaluationFeature.GAP_QUALITY: 50.0,
        EvaluationFeature.KING_TRAP_PENALTY: -200.0,
        EvaluationFeature.ROW_BALANCE: 25.0,
        EvaluationFeature.RESHUFFLE_POTENTIAL: 10.0,
        EvaluationFeature.MOVE_AVAILABILITY: 20.0,
    }
    
    def __init__(self, weights: Dict[EvaluationFeature, float] = None):
        """
        Initialize position evaluator.
        
        Args:
            weights: Custom weights for evaluation features
        """
        self.weights = weights or self.DEFAULT_WEIGHTS.copy()
    
    def evaluate_position(self, state: GameState) -> EvaluationResult:
        """
        Evaluate a game position with detailed feature breakdown.
        
        Args:
            state: Game state to evaluate
            
        Returns:
            Detailed evaluation result
        """
        feature_scores = {}
        
        # Check for terminal conditions first
        is_winning = state.is_winning_position()
        if is_winning:
            return EvaluationResult(
                total_score=10000.0,  # Maximum winning score
                feature_scores={f: 0.0 for f in EvaluationFeature},
                is_winning=True,
                is_terminal=True
            )
        
        # Calculate individual feature scores
        feature_scores[EvaluationFeature.SEQUENCE_PROGRESS] = self._evaluate_sequence_progress(state)
        feature_scores[EvaluationFeature.GAP_QUALITY] = self._evaluate_gap_quality(state)
        feature_scores[EvaluationFeature.KING_TRAP_PENALTY] = self._evaluate_king_traps(state)
        feature_scores[EvaluationFeature.ROW_BALANCE] = self._evaluate_row_balance(state)
        feature_scores[EvaluationFeature.RESHUFFLE_POTENTIAL] = self._evaluate_reshuffle_potential(state)
        feature_scores[EvaluationFeature.MOVE_AVAILABILITY] = self._evaluate_move_availability(state)
        
        # Calculate weighted total score
        total_score = sum(
            self.weights[feature] * score
            for feature, score in feature_scores.items()
        )
        
        # Check if position is terminal (no moves available)
        from .move_gen import MoveGenerator
        move_gen = MoveGenerator()
        is_terminal = move_gen.get_move_count(state) == 0
        
        return EvaluationResult(
            total_score=total_score,
            feature_scores=feature_scores,
            is_winning=False,
            is_terminal=is_terminal
        )
    
    def _evaluate_sequence_progress(self, state: GameState) -> float:
        """
        Evaluate progress of correctly placed sequences.
        
        Rewards:
        - Longer sequences
        - Sequences starting with 2 in first column
        - Multiple sequences across different rows
        """
        score = 0.0
        immutable_positions = state.get_immutable_positions()
        
        for row in range(state.ROWS):
            sequence_length = 0
            sequence_bonus = 0.0
            
            for col in range(state.COLS):
                if (row, col) in immutable_positions:
                    card = state.get_card(row, col)
                    if card is not None:
                        sequence_length += 1
                        # Exponential bonus for longer sequences
                        sequence_bonus += sequence_length ** 1.5
                else:
                    break  # End of sequence
            
            score += sequence_bonus
            
            # Special bonus for sequences starting properly (2 in first column)
            if sequence_length > 0:
                first_card = state.get_card(row, 0)
                if first_card and first_card.rank == Rank.TWO:
                    score += 20.0  # Starting sequence bonus
        
        return score
    
    def _evaluate_gap_quality(self, state: GameState) -> float:
        """
        Evaluate the quality and usefulness of current gap positions.
        
        Rewards:
        - Gaps that can be filled to extend sequences
        - Gaps in first column (for placing 2s)
        
        Penalizes:
        - Gaps that cannot be filled (after Kings or other gaps)
        """
        score = 0.0
        gaps = state.get_gaps()
        
        for gap_row, gap_col in gaps:
            if gap_col == 0:
                # First column gaps are valuable for starting sequences
                score += 15.0
            else:
                left_card = state.get_card(gap_row, gap_col - 1)
                if left_card is None:
                    # Gap after gap - penalize
                    score -= 10.0
                elif left_card.rank == Rank.KING:
                    # Gap after King - heavily penalize
                    score -= 25.0
                else:
                    # Useful gap that can extend a sequence
                    # Higher value for gaps that extend longer sequences
                    sequence_length = self._count_sequence_length_at_position(state, gap_row, gap_col - 1)
                    score += 5.0 + sequence_length * 2.0
        
        return score
    
    def _evaluate_king_traps(self, state: GameState) -> float:
        """
        Penalize King trap situations where gaps are created after Kings.
        
        King traps are permanent dead ends that reduce future move options.
        """
        penalty = 0.0
        
        for row in range(state.ROWS):
            for col in range(state.COLS - 1):  # Don't check last column
                card = state.get_card(row, col)
                next_card = state.get_card(row, col + 1)
                
                if card and card.rank == Rank.KING and next_card is None:
                    # Gap immediately after King
                    penalty += 1.0
        
        return penalty  # This will be multiplied by negative weight
    
    def _evaluate_row_balance(self, state: GameState) -> float:
        """
        Evaluate balance of progress across all four rows.
        
        Balanced progress maximizes reshuffle potential and strategic options.
        """
        row_progress = []
        
        for row in range(state.ROWS):
            progress = 0
            for col in range(state.COLS):
                card = state.get_card(row, col)
                if card is not None:
                    # Simple progress metric: count non-gap positions
                    # Could be enhanced to consider sequence correctness
                    progress += 1
            row_progress.append(progress)
        
        if not row_progress:
            return 0.0
        
        # Calculate variance - lower variance means better balance
        avg_progress = sum(row_progress) / len(row_progress)
        variance = sum((p - avg_progress) ** 2 for p in row_progress) / len(row_progress)
        
        # Convert variance to score (lower variance = higher score)
        return max(0.0, 20.0 - variance)
    
    def _evaluate_reshuffle_potential(self, state: GameState) -> float:
        """
        Evaluate potential for beneficial reshuffles.
        
        Considers:
        - Number of cards available for reshuffle
        - Distribution of cards by suit
        - Potential sequence starts
        """
        score = 0.0
        immutable_positions = state.get_immutable_positions()
        
        # Count non-immutable cards (available for reshuffle)
        reshuffle_cards = 0
        suit_counts = {suit: 0 for suit in Suit}
        
        for row in range(state.ROWS):
            for col in range(state.COLS):
                if (row, col) not in immutable_positions:
                    card = state.get_card(row, col)
                    if card is not None:
                        reshuffle_cards += 1
                        suit_counts[card.suit] += 1
        
        # More cards available for reshuffle = more options
        score += reshuffle_cards * 0.5
        
        # Balanced suit distribution is beneficial
        if reshuffle_cards > 0:
            suit_balance = min(suit_counts.values()) / max(suit_counts.values()) if max(suit_counts.values()) > 0 else 0
            score += suit_balance * 10.0
        
        return score
    
    def _evaluate_move_availability(self, state: GameState) -> float:
        """
        Evaluate the number and quality of available moves.
        
        More legal moves generally indicate better strategic options.
        """
        from .move_gen import MoveGenerator
        move_gen = MoveGenerator()
        move_count = move_gen.get_move_count(state)
        
        # Diminishing returns for more moves
        if move_count == 0:
            return -50.0  # Terminal position penalty
        else:
            return min(move_count * 5.0, 20.0)  # Cap at 4 moves
    
    def _count_sequence_length_at_position(self, state: GameState, row: int, col: int) -> int:
        """
        Count the length of a correct sequence ending at the given position.
        
        Args:
            state: Game state
            row: Row position
            col: Column position
            
        Returns:
            Length of sequence ending at this position
        """
        card = state.get_card(row, col)
        if card is None:
            return 0
        
        length = 1
        current_rank = card.rank.value
        current_suit = card.suit
        
        # Count backwards to find sequence start
        for check_col in range(col - 1, -1, -1):
            check_card = state.get_card(row, check_col)
            if (check_card and 
                check_card.rank.value == current_rank - 1 and 
                check_card.suit == current_suit):
                length += 1
                current_rank -= 1
            else:
                break
        
        return length


def create_evaluator(weights: Dict[EvaluationFeature, float] = None) -> PositionEvaluator:
    """
    Factory function to create a PositionEvaluator instance.
    
    This follows the dependency injection principle for better testability
    and allows for easy customization of evaluation weights.
    
    Args:
        weights: Custom weights for evaluation features
        
    Returns:
        Configured PositionEvaluator instance
    """
    return PositionEvaluator(weights)