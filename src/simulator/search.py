"""
Sequential minimax search implementation for Gaps Solitaire.

This module provides the MinimaxSearch class that handles sequential move search
for single-player games, exploring move sequences up to a specified depth.
"""

from typing import Optional, Tuple, List
import time
import logging
from pathlib import Path
from .game_state import GameState, CardPosition
from .move_executor import MoveExecutor
from .evaluator import PositionEvaluator

# Type alias for move representation
Move = Tuple[CardPosition, Tuple[int, int]]


class SearchDiagnostics:
    """Comprehensive diagnostic logging for search operations"""

    def __init__(self, log_file_path: str = "debug/search_diagnostics.log", 
                 log_level: int = logging.INFO):
        self.log_file_path = Path(log_file_path)
        self.log_file_path.parent.mkdir(exist_ok=True)

        # Configure logging
        self.logger = logging.getLogger("SearchDiagnostics")
        self.logger.setLevel(log_level)

        # Remove existing handlers to avoid duplicates
        self.logger.handlers.clear()

        # File handler
        file_handler = logging.FileHandler(self.log_file_path, mode='w')
        file_handler.setLevel(log_level)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        # Performance tracking
        self.search_times = []
        self.positions_per_second_history = []
        self.depth_samples = []
        self.branching_factor_samples = []

    def log_search_completion(self, positions_evaluated: int, time_taken: float, 
                            max_depth_reached: int, average_depth: float, 
                            average_branching_factor: float):
        """Log search completion with performance metrics"""
        positions_per_second = positions_evaluated / max(time_taken, 1e-9)
        
        self.logger.info("=== Search Completed ===")
        self.logger.info(f"Positions evaluated: {positions_evaluated}")
        self.logger.info(f"Time taken: {time_taken:.6f}s")
        self.logger.info(f"Positions/second: {positions_per_second:.2f}")
        self.logger.info(f"Max depth reached: {max_depth_reached}")
        self.logger.info(f"Average depth reached: {average_depth:.2f}")
        self.logger.info(f"Average branching factor: {average_branching_factor:.2f}")
        
        # Track for averages
        self.search_times.append(time_taken)
        self.positions_per_second_history.append(positions_per_second)
        self.depth_samples.append(average_depth)
        self.branching_factor_samples.append(average_branching_factor)

    def log_performance_summary(self):
        """Log aggregate performance metrics"""
        if not self.search_times:
            return
            
        avg_time = sum(self.search_times) / len(self.search_times)
        avg_positions_per_second = sum(self.positions_per_second_history) / len(self.positions_per_second_history)
        avg_depth = sum(self.depth_samples) / len(self.depth_samples)
        avg_branching = sum(self.branching_factor_samples) / len(self.branching_factor_samples)
        
        self.logger.info("=== Performance Summary ===")
        self.logger.info(f"Average search time: {avg_time:.6f}s")
        self.logger.info(f"Average positions/second: {avg_positions_per_second:.2f}")
        self.logger.info(f"Average depth reached: {avg_depth:.2f}")
        self.logger.info(f"Average branching factor: {avg_branching:.2f}")
        self.logger.info(f"Total searches: {len(self.search_times)}")

    def log_search_start(self, initial_position_info: str, max_depth: int):
        """Log search initialization"""
        self.logger.info("=== Search Started ===")
        self.logger.info(f"Position: {initial_position_info}")
        self.logger.info(f"Max search depth: {max_depth}")

    def log_node_evaluation(self, depth: int, legal_moves_count: int):
        """Log details about node evaluation for debugging"""
        # Only log at higher verbosity to reduce overhead
        if self.logger.isEnabledFor(logging.DEBUG):
            self.logger.debug(f"Evaluating node at depth {depth} with {legal_moves_count} legal moves")

    def log_pruned_node(self, depth: int, alpha: float, beta: float):
        """Log when a node is pruned by alpha-beta"""
        if self.logger.isEnabledFor(logging.DEBUG):
            self.logger.debug(f"Pruned node at depth {depth} (alpha={alpha:.3f}, beta={beta:.3f})")
        # Also log at info level for statistics
        self.logger.info(f"Alpha-beta pruning at depth {depth}")


class MinimaxSearch:
    """
    Sequential minimax search for single-player Gaps Solitaire.
    
    Explores move sequences up to a specified depth to find optimal play.
    Focused solely on search logic while using existing components for
    move execution and position evaluation.
    """
    
    def __init__(self, enable_diagnostics: bool = False):
        """Initialize search components and performance tracking."""
        self.move_executor = MoveExecutor()
        self.evaluator = PositionEvaluator()
        
        # Performance metrics
        self.nodes_searched = 0
        self.terminal_nodes = 0
        self.pruned_nodes = 0
        self.max_depth_reached = 0
        self.search_time = 0.0
        
        # Additional metrics for diagnostics
        self.depth_sum = 0  # Sum of all node depths for average calculation
        self.branching_factor_sum = 0  # Sum of legal moves at each node
        self.nodes_with_moves = 0  # Count of nodes that had legal moves
        
        # Diagnostic logging
        self.diagnostics = SearchDiagnostics() if enable_diagnostics else None
    
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
        self.pruned_nodes = 0
        self.max_depth_reached = 0
        self.depth_sum = 0
        self.branching_factor_sum = 0
        self.nodes_with_moves = 0
        
        start_time = time.perf_counter()
        
        # Log search start if diagnostics enabled
        if self.diagnostics:
            legal_moves = game_state.get_legal_moves()
            position_info = f"{len(legal_moves)} legal moves available"
            self.diagnostics.log_search_start(position_info, depth)
        
        try:
            # Get legal moves from current position
            legal_moves = game_state.get_legal_moves()
            
            if not legal_moves:
                # No moves available
                self.terminal_nodes = 1
                if self.diagnostics:
                    self.diagnostics.log_search_completion(0, 0.0, 0, 0.0, 0.0)
                return None
            
            best_move = None
            best_score = float('-inf')
            
            # For single-player search, we can use a form of aspiration search
            # Set a reasonable upper bound for beta based on evaluation range
            initial_beta = 2.0  # Just above typical scores to enable some pruning
            
            # Evaluate each possible first move
            for move in legal_moves:
                try:
                    # Execute the move to get new state
                    new_state = self.move_executor.execute_move(game_state, move)
                    
                    # Search deeper from this position with alpha-beta bounds
                    # Pass the current best score as alpha (lower bound)
                    score = self._minimax(new_state, depth - 1, 1, best_score, initial_beta)
                    
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
            
            # Log search completion if diagnostics enabled
            if self.diagnostics:
                # Calculate averages
                avg_depth = self.depth_sum / max(self.nodes_searched, 1)
                avg_branching_factor = self.branching_factor_sum / max(self.nodes_with_moves, 1)
                
                self.diagnostics.log_search_completion(
                    self.nodes_searched,
                    self.search_time,
                    self.max_depth_reached,
                    avg_depth,
                    avg_branching_factor
                )
    
    def _minimax(self, game_state: GameState, depth: int, current_depth: int, alpha: float, beta: float) -> float:
        """
        Recursive minimax search for sequential moves with alpha-beta pruning.
        
        For single-player search, alpha represents the best score found so far,
        and beta represents a cutoff threshold above which we can stop searching.
        
        Args:
            game_state: Current game state
            depth: Remaining search depth
            current_depth: Current depth from root (for tracking)
            alpha: Best score found so far (lower bound)
            beta: Cutoff threshold (upper bound)
            
        Returns:
            float: Evaluation score for this position
        """
        self.nodes_searched += 1
        self.max_depth_reached = max(self.max_depth_reached, current_depth)
        self.depth_sum += current_depth
        
        # Get legal moves
        legal_moves = game_state.get_legal_moves()
        
        # Track branching factor for diagnostics
        if legal_moves:
            self.branching_factor_sum += len(legal_moves)
            self.nodes_with_moves += 1
            
        # Log node evaluation if diagnostics enabled and debug level is on
        if self.diagnostics and self.diagnostics.logger.isEnabledFor(logging.DEBUG):
            self.diagnostics.log_node_evaluation(current_depth, len(legal_moves))
        
        # Terminal condition: no legal moves or depth limit reached
        if not legal_moves or depth <= 0:
            self.terminal_nodes += 1
            return self.evaluator.evaluate(game_state)
        
        # For single-player sequential search, we want the maximum score
        # from continuing to make moves
        best_score = float('-inf')
        local_alpha = alpha
        
        for move in legal_moves:
            try:
                # Execute move to get new state
                new_state = self.move_executor.execute_move(game_state, move)
                
                # Recurse deeper with updated alpha bound
                score = self._minimax(new_state, depth - 1, current_depth + 1, local_alpha, beta)
                
                # Track best score and update alpha
                if score > best_score:
                    best_score = score
                    local_alpha = max(local_alpha, score)
                
                # Alpha-beta pruning: if current best score >= beta,
                # we can prune remaining moves
                if best_score >= beta:
                    # Beta cutoff - we've found a move good enough
                    self.pruned_nodes += 1
                    if self.diagnostics:
                        self.diagnostics.log_pruned_node(current_depth, local_alpha, beta)
                    break
                
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
            'pruned_nodes': self.pruned_nodes,
            'max_depth_reached': self.max_depth_reached,
            'search_time': self.search_time,
            'nodes_per_second': self.nodes_searched / max(self.search_time, 1e-9)
        }