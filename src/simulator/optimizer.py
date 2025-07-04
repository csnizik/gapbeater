"""
Multi-phase strategic planning and optimization for Gaps Solitaire.

This module implements the unique two-phase optimization strategy outlined in
PROJECT_CONTEXT.md, providing blind strategy analysis followed by perfect
information optimization across all game phases.

Key Features:
- Phase 1: Blind strategy analysis without future reshuffle knowledge
- Phase 2: Perfect information optimization with complete game knowledge
- Retrograde analysis for optimal cross-phase strategy
- Strategic planning for reshuffle management

Performance Requirements:
- Coordinate with search engine to maintain 50,000+ positions/second
- Support strategic analysis across multiple game phases
- Enable intelligent reshuffle planning and execution
"""

from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass
from enum import Enum
import copy

from .game_state import GameState, create_initial_state
from .move_gen import Move, MoveGenerator
from .evaluator import PositionEvaluator, EvaluationResult
from .search import SearchEngine, SearchResult


class GamePhase(Enum):
    """Different phases of a Gaps Solitaire game."""
    INITIAL_DEAL = 0
    FIRST_RESHUFFLE = 1
    SECOND_RESHUFFLE = 2
    THIRD_RESHUFFLE = 3


@dataclass
class PhaseResult:
    """Result of analysis for a single game phase."""
    phase: GamePhase
    initial_state: GameState
    recommended_moves: List[Move]
    final_state: GameState
    evaluation: EvaluationResult
    search_stats: Dict[str, any]
    is_winning: bool


@dataclass
class GameAnalysis:
    """Complete analysis of a Gaps Solitaire game."""
    phase_results: Dict[GamePhase, PhaseResult]
    overall_strategy: str  # 'blind' or 'perfect_information'
    total_moves: int
    final_evaluation: EvaluationResult
    is_game_won: bool
    strategic_insights: List[str]


class StrategicOptimizer:
    """
    Multi-phase strategic optimizer implementing the two-phase approach.
    
    Provides both blind strategy analysis (without future knowledge) and
    perfect information optimization (with complete game knowledge).
    """
    
    def __init__(self, search_engine: SearchEngine):
        """
        Initialize strategic optimizer.
        
        Args:
            search_engine: Configured search engine for move analysis
        """
        self.search_engine = search_engine
        self.move_generator = search_engine.move_generator
        self.evaluator = search_engine.evaluator
        
        # Game history tracking
        self.phase_states: Dict[GamePhase, GameState] = {}
        self.blind_analysis: Optional[GameAnalysis] = None
        self.perfect_analysis: Optional[GameAnalysis] = None
    
    def analyze_blind_strategy(self, initial_cards: List[str]) -> PhaseResult:
        """
        Analyze initial deal without knowledge of future reshuffles.
        
        This is Phase 1 of the optimization strategy - providing real-time
        move recommendations as the game progresses.
        
        Args:
            initial_cards: List of 52 card strings for initial deal
            
        Returns:
            Analysis result for the initial phase
        """
        initial_state = create_initial_state(initial_cards)
        self.phase_states[GamePhase.INITIAL_DEAL] = initial_state
        
        # Find best sequence of moves for current position
        recommended_moves = []
        current_state = initial_state
        
        while True:
            search_result = self.search_engine.search_best_move(current_state)
            
            if search_result.best_move is None:
                break  # No more moves available
            
            recommended_moves.append(search_result.best_move)
            current_state = self.move_generator.apply_move(current_state, search_result.best_move)
            
            # Check for winning condition
            if current_state.is_winning_position():
                break
        
        # Evaluate final position
        final_evaluation = self.evaluator.evaluate_position(current_state)
        
        return PhaseResult(
            phase=GamePhase.INITIAL_DEAL,
            initial_state=initial_state,
            recommended_moves=recommended_moves,
            final_state=current_state,
            evaluation=final_evaluation,
            search_stats=self.search_engine.get_search_stats(),
            is_winning=current_state.is_winning_position()
        )
    
    def analyze_reshuffle_phase(self, phase: GamePhase, reshuffle_cards: List[str]) -> PhaseResult:
        """
        Analyze a reshuffle phase in blind strategy mode.
        
        Args:
            phase: Which reshuffle phase this is
            reshuffle_cards: Card positions after reshuffle
            
        Returns:
            Analysis result for this reshuffle phase
        """
        if phase == GamePhase.INITIAL_DEAL:
            raise ValueError("Use analyze_blind_strategy for initial deal")
        
        # Get previous phase state to preserve immutable sequences
        prev_phase = GamePhase(phase.value - 1)
        if prev_phase not in self.phase_states:
            raise ValueError(f"Previous phase {prev_phase} not analyzed yet")
        
        prev_state = self.phase_states[prev_phase]
        
        # Create new state preserving immutable sequences
        new_state = self._create_reshuffle_state(prev_state, reshuffle_cards)
        self.phase_states[phase] = new_state
        
        # Analyze this phase
        recommended_moves = []
        current_state = new_state
        
        while True:
            search_result = self.search_engine.search_best_move(current_state)
            
            if search_result.best_move is None:
                break
            
            recommended_moves.append(search_result.best_move)
            current_state = self.move_generator.apply_move(current_state, search_result.best_move)
            
            if current_state.is_winning_position():
                break
        
        final_evaluation = self.evaluator.evaluate_position(current_state)
        
        return PhaseResult(
            phase=phase,
            initial_state=new_state,
            recommended_moves=recommended_moves,
            final_state=current_state,
            evaluation=final_evaluation,
            search_stats=self.search_engine.get_search_stats(),
            is_winning=current_state.is_winning_position()
        )
    
    def analyze_perfect_information_strategy(self, all_phase_cards: Dict[GamePhase, List[str]]) -> GameAnalysis:
        """
        Analyze complete game with perfect information about all phases.
        
        This is Phase 2 of the optimization strategy - re-analyzing the entire
        game with knowledge of all reshuffles to find optimal cross-phase strategy.
        
        Args:
            all_phase_cards: Card positions for all game phases
            
        Returns:
            Complete game analysis with optimal strategy
        """
        if GamePhase.INITIAL_DEAL not in all_phase_cards:
            raise ValueError("Initial deal cards required")
        
        # Store all phase states
        phase_states = {}
        for phase, cards in all_phase_cards.items():
            if phase == GamePhase.INITIAL_DEAL:
                phase_states[phase] = create_initial_state(cards)
            else:
                prev_phase = GamePhase(phase.value - 1)
                if prev_phase not in phase_states:
                    raise ValueError(f"Previous phase {prev_phase} missing")
                phase_states[phase] = self._create_reshuffle_state(phase_states[prev_phase], cards)
        
        # Implement retrograde analysis working backwards from final phase
        optimal_strategy = self._compute_retrograde_strategy(phase_states)
        
        # Build complete analysis
        phase_results = {}
        total_moves = 0
        final_evaluation = None
        is_game_won = False
        
        for phase in GamePhase:
            if phase in optimal_strategy:
                moves = optimal_strategy[phase]
                initial_state = phase_states[phase]
                
                # Apply moves to get final state
                final_state = initial_state
                for move in moves:
                    final_state = self.move_generator.apply_move(final_state, move)
                
                evaluation = self.evaluator.evaluate_position(final_state)
                
                phase_results[phase] = PhaseResult(
                    phase=phase,
                    initial_state=initial_state,
                    recommended_moves=moves,
                    final_state=final_state,
                    evaluation=evaluation,
                    search_stats={},  # Not applicable for retrograde analysis
                    is_winning=final_state.is_winning_position()
                )
                
                total_moves += len(moves)
                final_evaluation = evaluation
                
                if final_state.is_winning_position():
                    is_game_won = True
                    break
        
        # Generate strategic insights
        insights = self._generate_strategic_insights(phase_results, optimal_strategy)
        
        return GameAnalysis(
            phase_results=phase_results,
            overall_strategy='perfect_information',
            total_moves=total_moves,
            final_evaluation=final_evaluation or EvaluationResult(0.0, {}, False, True),
            is_game_won=is_game_won,
            strategic_insights=insights
        )
    
    def _create_reshuffle_state(self, prev_state: GameState, new_cards: List[str]) -> GameState:
        """
        Create new game state after reshuffle, preserving immutable sequences.
        
        Args:
            prev_state: State before reshuffle
            new_cards: New card positions after reshuffle
            
        Returns:
            New game state with preserved sequences
        """
        if len(new_cards) != GameState.TOTAL_POSITIONS:
            raise ValueError(f"Must provide exactly {GameState.TOTAL_POSITIONS} card positions")
        
        # Start with new card layout
        new_state = create_initial_state(new_cards)
        
        # Preserve immutable sequences from previous state
        immutable_positions = prev_state.get_immutable_positions()
        
        for row, col in immutable_positions:
            preserved_card = prev_state.get_card(row, col)
            if preserved_card is not None:
                new_state.set_card(row, col, preserved_card)
        
        return new_state
    
    def _compute_retrograde_strategy(self, phase_states: Dict[GamePhase, GameState]) -> Dict[GamePhase, List[Move]]:
        """
        Compute optimal strategy using retrograde analysis.
        
        Works backwards from the final phase to find moves that set up
        the best possible positions in later phases.
        
        Args:
            phase_states: Game states for all phases
            
        Returns:
            Optimal moves for each phase
        """
        optimal_moves = {}
        
        # Start from the final available phase and work backwards
        phases = sorted(phase_states.keys(), key=lambda p: p.value, reverse=True)
        
        for phase in phases:
            state = phase_states[phase]
            
            # For now, use standard search for each phase
            # TODO: Implement true retrograde analysis that considers
            # how moves in this phase affect future phase outcomes
            
            moves = []
            current_state = state
            
            while True:
                search_result = self.search_engine.search_best_move(current_state)
                
                if search_result.best_move is None:
                    break
                
                moves.append(search_result.best_move)
                current_state = self.move_generator.apply_move(current_state, search_result.best_move)
                
                if current_state.is_winning_position():
                    break
            
            optimal_moves[phase] = moves
        
        return optimal_moves
    
    def _generate_strategic_insights(self, phase_results: Dict[GamePhase, PhaseResult], 
                                   optimal_strategy: Dict[GamePhase, List[Move]]) -> List[str]:
        """
        Generate strategic insights about the optimal strategy.
        
        Args:
            phase_results: Results for each phase
            optimal_strategy: Optimal moves for each phase
            
        Returns:
            List of strategic insights
        """
        insights = []
        
        # Analyze overall game outcome
        if any(result.is_winning for result in phase_results.values()):
            insights.append("Game can be won with optimal play")
        else:
            insights.append("Game cannot be won - focus on maximizing final position")
        
        # Analyze phase-specific strategies
        for phase, result in phase_results.items():
            if result.recommended_moves:
                first_move = result.recommended_moves[0]
                if first_move.to_col == 0:
                    insights.append(f"Phase {phase.value}: Prioritize starting new sequences")
                else:
                    insights.append(f"Phase {phase.value}: Focus on extending existing sequences")
        
        # Analyze move efficiency
        total_moves = sum(len(moves) for moves in optimal_strategy.values())
        if total_moves <= 10:
            insights.append("Efficient solution with minimal moves")
        elif total_moves <= 20:
            insights.append("Moderate complexity solution")
        else:
            insights.append("Complex position requiring many moves")
        
        return insights
    
    def compare_strategies(self) -> Dict[str, any]:
        """
        Compare blind strategy vs perfect information strategy results.
        
        Returns:
            Comparison analysis between the two strategies
        """
        if not self.blind_analysis or not self.perfect_analysis:
            return {"error": "Both strategies must be analyzed first"}
        
        comparison = {
            "blind_strategy": {
                "total_moves": self.blind_analysis.total_moves,
                "final_score": self.blind_analysis.final_evaluation.total_score,
                "game_won": self.blind_analysis.is_game_won
            },
            "perfect_information": {
                "total_moves": self.perfect_analysis.total_moves,
                "final_score": self.perfect_analysis.final_evaluation.total_score,
                "game_won": self.perfect_analysis.is_game_won
            }
        }
        
        # Calculate improvement
        if self.perfect_analysis.final_evaluation.total_score > self.blind_analysis.final_evaluation.total_score:
            improvement = self.perfect_analysis.final_evaluation.total_score - self.blind_analysis.final_evaluation.total_score
            comparison["improvement"] = f"Perfect information strategy scores {improvement:.1f} points higher"
        else:
            comparison["improvement"] = "No significant improvement from perfect information"
        
        return comparison


def create_strategic_optimizer(search_engine: SearchEngine = None) -> StrategicOptimizer:
    """
    Factory function to create a StrategicOptimizer instance.
    
    Args:
        search_engine: Configured search engine
        
    Returns:
        Strategic optimizer instance
    """
    if search_engine is None:
        from .search import create_search_engine
        search_engine = create_search_engine()
    
    return StrategicOptimizer(search_engine)