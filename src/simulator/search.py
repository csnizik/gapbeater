"""
Tree search algorithms for Gaps Solitaire optimization.

This module implements chess engine search techniques adapted for single-player
solitaire, following the performance targets and algorithmic approaches outlined
in PROJECT_CONTEXT.md.

Key Algorithms:
- Modified Minimax for single-player optimization
- Alpha-Beta Pruning for search efficiency
- Iterative Deepening for anytime algorithm behavior
- Transposition Tables for position caching
- Move Ordering for search optimization

Performance Requirements:
- 50,000+ position evaluations per second
- <2 second response times for move recommendations
- Support for search depths of 15+ moves
"""

from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum
import time
from collections import defaultdict

from .game_state import GameState
from .move_gen import Move, MoveGenerator
from .evaluator import PositionEvaluator, EvaluationResult


class SearchResult:
    """Result of a search operation."""
    
    def __init__(self, best_move: Optional[Move], score: float, depth: int, 
                 nodes_searched: int, time_elapsed: float, principal_variation: List[Move] = None):
        self.best_move = best_move
        self.score = score
        self.depth = depth
        self.nodes_searched = nodes_searched
        self.time_elapsed = time_elapsed
        self.principal_variation = principal_variation or []
    
    def __str__(self) -> str:
        """String representation of search result."""
        lines = [
            f"Best Move: {self.best_move.to_compact_string() if self.best_move else 'None'}",
            f"Score: {self.score:.2f}",
            f"Depth: {self.depth}",
            f"Nodes: {self.nodes_searched:,}",
            f"Time: {self.time_elapsed:.3f}s",
            f"NPS: {self.nodes_searched / max(self.time_elapsed, 0.001):,.0f}"
        ]
        
        if self.principal_variation:
            pv_str = " -> ".join(move.to_compact_string() for move in self.principal_variation[:5])
            if len(self.principal_variation) > 5:
                pv_str += "..."
            lines.append(f"PV: {pv_str}")
        
        return "\n".join(lines)


@dataclass
class TranspositionEntry:
    """Entry in the transposition table."""
    score: float
    depth: int
    best_move: Optional[Move]
    node_type: str  # 'exact', 'lower', 'upper'


class SearchEngine:
    """
    Tree search engine implementing chess engine techniques for Gaps Solitaire.
    
    Provides iterative deepening search with alpha-beta pruning, transposition
    tables, and move ordering for optimal performance.
    """
    
    def __init__(self, move_generator: MoveGenerator, evaluator: PositionEvaluator,
                 max_time: float = 2.0, max_depth: int = 20):
        """
        Initialize search engine.
        
        Args:
            move_generator: Move generation component
            evaluator: Position evaluation component
            max_time: Maximum search time in seconds
            max_depth: Maximum search depth
        """
        self.move_generator = move_generator
        self.evaluator = evaluator
        self.max_time = max_time
        self.max_depth = max_depth
        
        # Search statistics
        self.nodes_searched = 0
        self.start_time = 0.0
        
        # Transposition table
        self.transposition_table: Dict[int, TranspositionEntry] = {}
        self.tt_hits = 0
        
        # Move ordering helpers
        self.killer_moves: Dict[int, List[Move]] = defaultdict(list)
        self.history_scores: Dict[Tuple[int, int, int, int], int] = defaultdict(int)
    
    def search_best_move(self, state: GameState, max_time: float = None, 
                        max_depth: int = None) -> SearchResult:
        """
        Find the best move using iterative deepening search.
        
        Args:
            state: Current game state
            max_time: Maximum search time (overrides default)
            max_depth: Maximum search depth (overrides default)
            
        Returns:
            Search result with best move and analysis
        """
        search_time = max_time or self.max_time
        search_depth = max_depth or self.max_depth
        
        self.start_time = time.time()
        self.nodes_searched = 0
        self.tt_hits = 0
        
        best_move = None
        best_score = float('-inf')
        principal_variation = []
        
        # Iterative deepening loop
        for depth in range(1, search_depth + 1):
            if self._time_up():
                break
            
            try:
                result = self._search_depth(state, depth)
                
                # Update best result if search completed
                if result.best_move is not None:
                    best_move = result.best_move
                    best_score = result.score
                    principal_variation = result.principal_variation
                
                # Stop if we found a winning move
                if best_score >= 9000:  # Near winning score
                    break
                    
            except TimeoutError:
                break
        
        elapsed_time = time.time() - self.start_time
        
        return SearchResult(
            best_move=best_move,
            score=best_score,
            depth=depth - 1,  # Last completed depth
            nodes_searched=self.nodes_searched,
            time_elapsed=elapsed_time,
            principal_variation=principal_variation
        )
    
    def _search_depth(self, state: GameState, depth: int) -> SearchResult:
        """
        Search to a specific depth.
        
        Args:
            state: Current game state
            depth: Target search depth
            
        Returns:
            Search result for this depth
        """
        principal_variation = []
        
        score = self._search(state, depth, float('-inf'), float('inf'), 
                           principal_variation, is_root=True)
        
        best_move = principal_variation[0] if principal_variation else None
        
        return SearchResult(
            best_move=best_move,
            score=score,
            depth=depth,
            nodes_searched=self.nodes_searched,
            time_elapsed=time.time() - self.start_time,
            principal_variation=principal_variation
        )
    
    def _search(self, state: GameState, depth: int, alpha: float, beta: float,
               principal_variation: List[Move], is_root: bool = False) -> float:
        """
        Recursive search with alpha-beta pruning.
        
        Args:
            state: Current game state
            depth: Remaining search depth
            alpha: Alpha bound for pruning
            beta: Beta bound for pruning
            principal_variation: Principal variation being built
            is_root: Whether this is the root of the search
            
        Returns:
            Best score from this position
            
        Raises:
            TimeoutError: If search time limit exceeded
        """
        if self._time_up():
            raise TimeoutError("Search time limit exceeded")
        
        self.nodes_searched += 1
        
        # Check transposition table
        state_hash = state.get_zobrist_hash()
        tt_entry = self.transposition_table.get(state_hash)
        
        if (tt_entry and tt_entry.depth >= depth and not is_root):
            self.tt_hits += 1
            
            if tt_entry.node_type == 'exact':
                return tt_entry.score
            elif tt_entry.node_type == 'lower' and tt_entry.score >= beta:
                return tt_entry.score
            elif tt_entry.node_type == 'upper' and tt_entry.score <= alpha:
                return tt_entry.score
        
        # Terminal node evaluation
        if depth == 0:
            evaluation = self.evaluator.evaluate_position(state)
            return evaluation.total_score
        
        # Check for terminal position
        legal_moves = self.move_generator.generate_legal_moves(state)
        if not legal_moves:
            evaluation = self.evaluator.evaluate_position(state)
            return evaluation.total_score
        
        # Order moves for better pruning
        ordered_moves = self._order_moves(state, legal_moves, depth, tt_entry)
        
        best_score = float('-inf')
        best_move = None
        current_pv = []
        original_alpha = alpha
        
        for i, move in enumerate(ordered_moves):
            # Apply move
            new_state = self.move_generator.apply_move(state, move)
            
            # Recursive search
            child_pv = []
            score = self._search(new_state, depth - 1, alpha, beta, child_pv)
            
            # Update best score and move
            if score > best_score:
                best_score = score
                best_move = move
                current_pv = [move] + child_pv
            
            # Alpha-beta pruning
            alpha = max(alpha, score)
            if alpha >= beta:
                # Beta cutoff - update killer moves and history
                self._update_killer_moves(depth, move)
                self._update_history_score(move, depth)
                break
        
        # Store in transposition table
        node_type = 'exact'
        if best_score <= original_alpha:
            node_type = 'upper'
        elif best_score >= beta:
            node_type = 'lower'
        
        self.transposition_table[state_hash] = TranspositionEntry(
            score=best_score,
            depth=depth,
            best_move=best_move,
            node_type=node_type
        )
        
        # Update principal variation for root
        if is_root and current_pv:
            principal_variation.extend(current_pv)
        
        return best_score
    
    def _order_moves(self, state: GameState, moves: List[Move], depth: int, 
                    tt_entry: Optional[TranspositionEntry]) -> List[Move]:
        """
        Order moves for better search efficiency.
        
        Priority order:
        1. Transposition table move
        2. Killer moves
        3. History heuristic
        4. Static move evaluation
        """
        if not moves:
            return moves
        
        move_scores = []
        
        for move in moves:
            score = 0
            
            # Transposition table move gets highest priority
            if tt_entry and tt_entry.best_move == move:
                score += 10000
            
            # Killer moves
            if move in self.killer_moves.get(depth, []):
                score += 1000
            
            # History heuristic
            history_key = (move.from_row, move.from_col, move.to_row, move.to_col)
            score += self.history_scores.get(history_key, 0)
            
            # Static move evaluation (simple heuristics)
            score += self._evaluate_move_statically(state, move)
            
            move_scores.append((score, move))
        
        # Sort by score (descending)
        move_scores.sort(key=lambda x: x[0], reverse=True)
        
        return [move for score, move in move_scores]
    
    def _evaluate_move_statically(self, state: GameState, move: Move) -> float:
        """
        Simple static evaluation of a move for ordering purposes.
        
        Args:
            state: Current game state
            move: Move to evaluate
            
        Returns:
            Static evaluation score
        """
        score = 0.0
        
        # Prefer moves that extend sequences
        if move.to_col > 0:
            left_card = state.get_card(move.to_row, move.to_col - 1)
            if left_card and left_card.rank.value + 1 == move.card.rank.value:
                score += 50.0
        
        # Prefer moves to first column (starting sequences)
        if move.to_col == 0 and move.card.rank.value == 2:
            score += 30.0
        
        # Prefer moves that don't create gaps after Kings
        source_row, source_col = move.from_row, move.from_col
        if source_col > 0:
            left_of_source = state.get_card(source_row, source_col - 1)
            if left_of_source and left_of_source.rank.value == 13:  # King
                score -= 20.0
        
        return score
    
    def _update_killer_moves(self, depth: int, move: Move) -> None:
        """Update killer moves for the given depth."""
        killers = self.killer_moves[depth]
        if move not in killers:
            killers.insert(0, move)
            if len(killers) > 2:  # Keep only top 2 killers per depth
                killers.pop()
    
    def _update_history_score(self, move: Move, depth: int) -> None:
        """Update history score for the given move."""
        history_key = (move.from_row, move.from_col, move.to_row, move.to_col)
        self.history_scores[history_key] += depth * depth
    
    def _time_up(self) -> bool:
        """Check if search time limit has been exceeded."""
        return time.time() - self.start_time >= self.max_time
    
    def clear_search_cache(self) -> None:
        """Clear transposition table and search caches."""
        self.transposition_table.clear()
        self.killer_moves.clear()
        self.history_scores.clear()
        self.tt_hits = 0
    
    def get_search_stats(self) -> Dict[str, any]:
        """Get current search statistics."""
        elapsed = time.time() - self.start_time if self.start_time else 0
        return {
            'nodes_searched': self.nodes_searched,
            'tt_size': len(self.transposition_table),
            'tt_hits': self.tt_hits,
            'nps': self.nodes_searched / max(elapsed, 0.001),
            'time_elapsed': elapsed
        }


def create_search_engine(move_generator: MoveGenerator = None, 
                        evaluator: PositionEvaluator = None,
                        max_time: float = 2.0, max_depth: int = 20) -> SearchEngine:
    """
    Factory function to create a SearchEngine instance.
    
    This follows the dependency injection principle for better testability
    and allows for easy customization of search parameters.
    
    Args:
        move_generator: Move generation component
        evaluator: Position evaluation component
        max_time: Maximum search time in seconds
        max_depth: Maximum search depth
        
    Returns:
        Configured SearchEngine instance
    """
    if move_generator is None:
        from .move_gen import create_move_generator
        move_generator = create_move_generator()
    
    if evaluator is None:
        from .evaluator import create_evaluator
        evaluator = create_evaluator()
    
    return SearchEngine(move_generator, evaluator, max_time, max_depth)