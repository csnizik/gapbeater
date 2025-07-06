"""
Sequential minimax search implementation for Gaps Solitaire.

This module provides the MinimaxSearch class that handles sequential move search
for single-player games, exploring move sequences up to a specified depth.
"""

from typing import Optional, Tuple, List
import time
from .game_state import GameState, CardPosition
from .move_executor import MoveExecutor
from .evaluator import PositionEvaluator

# Type alias for move representation
Move = Tuple[CardPosition, Tuple[int, int]]


class MinimaxSearch:
    """
    Sequential minimax search for single-player Gaps Solitaire.
    
    Explores move sequences up to a specified depth to find optimal play.
    Focused solely on search logic while using existing components for
    move execution and position evaluation.
    """
    
    def __init__(self):
        """Initialize search components and performance tracking."""
        self.move_executor = MoveExecutor()
        self.evaluator = PositionEvaluator()
        
        # Performance metrics
        self.nodes_searched = 0
        self.terminal_nodes = 0
        self.max_depth_reached = 0
        self.search_time = 0.0
    
    def search(self, game_state: GameState, depth: int) -> Optional[Move]:
        """
        Search for the best move sequence from the given position.
        
        Args:
            game_state: Current game state to search from
            depth: Maximum depth to search (number of moves)
            
        Returns:
            Optional[Move]: First move of best sequence, or None if no moves available
        """
        # Reset performance metrics
        self.nodes_searched = 0
        self.terminal_nodes = 0
        self.max_depth_reached = 0
        
        start_time = time.perf_counter()
        
        try:
            # Get legal moves from current position
            legal_moves = game_state.get_legal_moves()
            
            if not legal_moves:
                # No moves available
                self.terminal_nodes = 1
                return None
            
            best_move = None
            best_score = float('-inf')
            
            # Evaluate each possible first move
            for move in legal_moves:
                try:
                    # Execute the move to get new state
                    new_state = self.move_executor.execute_move(game_state, move)
                    
                    # Search deeper from this position
                    score = self._minimax(new_state, depth - 1, 1)
                    
                    # Track best move
                    if score > best_score:
                        best_score = score
                        best_move = move
                        
                except Exception:
                    # Skip invalid moves
                    continue
            
            return best_move
            
        finally:
            self.search_time = time.perf_counter() - start_time
    
    def _minimax(self, game_state: GameState, depth: int, current_depth: int) -> float:
        """
        Recursive minimax search for sequential moves.
        
        Args:
            game_state: Current game state
            depth: Remaining search depth
            current_depth: Current depth from root (for tracking)
            
        Returns:
            float: Evaluation score for this position
        """
        self.nodes_searched += 1
        self.max_depth_reached = max(self.max_depth_reached, current_depth)
        
        # Get legal moves
        legal_moves = game_state.get_legal_moves()
        
        # Terminal condition: no legal moves or depth limit reached
        if not legal_moves or depth <= 0:
            self.terminal_nodes += 1
            return self.evaluator.evaluate(game_state)
        
        # For single-player sequential search, we want the maximum score
        # from continuing to make moves
        best_score = float('-inf')
        
        for move in legal_moves:
            try:
                # Execute move to get new state
                new_state = self.move_executor.execute_move(game_state, move)
                
                # Recurse deeper
                score = self._minimax(new_state, depth - 1, current_depth + 1)
                
                # Track best score
                best_score = max(best_score, score)
                
            except Exception:
                # Skip invalid moves
                continue
        
        # If no valid moves were found, evaluate current position
        if best_score == float('-inf'):
            self.terminal_nodes += 1
            return self.evaluator.evaluate(game_state)
        
        return best_score
    
    def get_performance_stats(self) -> dict:
        """
        Get performance statistics from the last search.
        
        Returns:
            dict: Performance metrics including nodes searched, time, etc.
        """
        return {
            'nodes_searched': self.nodes_searched,
            'terminal_nodes': self.terminal_nodes,
            'max_depth_reached': self.max_depth_reached,
            'search_time': self.search_time,
            'nodes_per_second': self.nodes_searched / max(self.search_time, 1e-9)
        }