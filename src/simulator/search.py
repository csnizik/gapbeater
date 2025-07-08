"""
Sequential minimax search implementation for Gaps Solitaire.

This module provides the MinimaxSearch class that handles sequential move search
for single-player games, exploring move sequences up to a specified depth.
"""

from typing import Optional, Tuple, List, Dict
import time
import logging
from pathlib import Path
from .game_state import GameState, CardPosition
from .move_executor import MoveExecutor
from .evaluator import PositionEvaluator
from ..settings import SEQUENCE_PREFERENCE_MULTIPLIER

# Type alias for move representation
Move = Tuple[CardPosition, Tuple[int, int]]


class SearchDiagnostics:
    """Comprehensive diagnostic logging for search operations"""

    def __init__(self, log_file_path: str = None,
                 log_level: int = logging.INFO):
        # Check if we should use timestamped directory
        if log_file_path is None:
            from ..config.settings_manager import SettingsManager
            settings_manager = SettingsManager()
            current_log_dir = settings_manager.get_current_log_directory()
            if current_log_dir:
                log_file_path = str(current_log_dir / "search_diagnostics.log")
            else:
                log_file_path = "debug/search_diagnostics.log"

        self.log_file_path = Path(log_file_path)
        self.log_file_path.parent.mkdir(parents=True, exist_ok=True)

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
                            average_branching_factor: float, cache_hits: int = 0,
                            cache_misses: int = 0, transposition_table_size: int = 0):
        """Log search completion with performance metrics"""
        positions_per_second = positions_evaluated / max(time_taken, 1e-9)
        total_cache_lookups = cache_hits + cache_misses
        cache_hit_rate = cache_hits / max(total_cache_lookups, 1) if total_cache_lookups > 0 else 0.0

        self.logger.info("=== Search Completed ===")
        self.logger.info(f"Positions evaluated: {positions_evaluated}")
        self.logger.info(f"Time taken: {time_taken:.6f}s")
        self.logger.info(f"Positions/second: {positions_per_second:.2f}")
        self.logger.info(f"Max depth reached: {max_depth_reached}")
        self.logger.info(f"Average depth reached: {average_depth:.2f}")
        self.logger.info(f"Average branching factor: {average_branching_factor:.2f}")

        # Log transposition table statistics
        if total_cache_lookups > 0:
            self.logger.info(f"Cache hits: {cache_hits}")
            self.logger.info(f"Cache misses: {cache_misses}")
            self.logger.info(f"Cache hit rate: {cache_hit_rate:.1%}")
            self.logger.info(f"Transposition table size: {transposition_table_size}")

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
        self.move_executor = MoveExecutor(enable_diagnostics=enable_diagnostics)
        self.evaluator = PositionEvaluator(enable_diagnostics=enable_diagnostics)

        # Performance metrics
        self.nodes_searched = 0
        self.terminal_nodes = 0
        self.pruned_nodes = 0
        self.max_depth_reached = 0
        self.search_time = 0.0
        self.completed_depth = 0  # Track deepest completed iteration in iterative deepening

        # Additional metrics for diagnostics
        self.depth_sum = 0  # Sum of all node depths for average calculation
        self.branching_factor_sum = 0  # Sum of legal moves at each node
        self.nodes_with_moves = 0  # Count of nodes that had legal moves

        # Transposition table for caching position evaluations
        self.transposition_table = {}  # Dict[int, float] - maps hash(game_state) -> evaluation score
        self.cache_hits = 0
        self.cache_misses = 0

        # Diagnostic logging
        self.diagnostics = SearchDiagnostics() if enable_diagnostics else None

    def search(self, game_state: GameState, max_depth: int = None) -> Optional[Move]:
        """
        Search for the best move using iterative deepening.

        Performs searches from depth=1 up to max_depth, returning the best move found
        from the deepest completed iteration. Stops early if time limit is reached.

        Args:
            game_state: Current game state to search from
            max_depth: Maximum depth to search (default: DEFAULT_SEARCH_DEPTH)

        Returns:
            Optional[Move]: Best move found, or None if no moves available
        """
        from src.settings import SEARCH_DEPTH as DEFAULT_SEARCH_DEPTH, SEARCH_TIME_LIMIT as MAX_SEARCH_TIME_SECONDS

        if max_depth is None:
            max_depth = DEFAULT_SEARCH_DEPTH

        # Reset cumulative performance metrics
        self.nodes_searched = 0
        self.terminal_nodes = 0
        self.pruned_nodes = 0
        self.max_depth_reached = 0
        self.completed_depth = 0
        self.depth_sum = 0
        self.branching_factor_sum = 0
        self.nodes_with_moves = 0

        # Clear transposition table to avoid stale entries between searches
        self.transposition_table.clear()
        self.cache_hits = 0
        self.cache_misses = 0

        search_start_time = time.perf_counter()

        # Get legal moves from current position
        legal_moves = game_state.get_legal_moves()

        if not legal_moves:
            # No moves available
            self.terminal_nodes = 1
            self.search_time = time.perf_counter() - search_start_time
            if self.diagnostics:
                self.diagnostics.log_search_completion(0, 0.0, 0, 0.0, 0.0, 0, 0, 0)
            return None

        # Log search start if diagnostics enabled
        if self.diagnostics:
            position_info = f"{len(legal_moves)} legal moves available"
            self.diagnostics.log_search_start(position_info, max_depth)

        best_move = None
        best_overall_score = float('-inf')
        completed_depth = 0

        try:
            # Iterative deepening loop
            for current_depth in range(1, max_depth + 1):
                depth_start_time = time.perf_counter()

                # Check if we have enough time for another iteration
                elapsed_time = depth_start_time - search_start_time
                if elapsed_time > MAX_SEARCH_TIME_SECONDS * 0.8:  # Stop at 80% of time limit
                    if self.diagnostics:
                        self.diagnostics.logger.info(f"Early termination: Time limit approaching ({elapsed_time:.3f}s)")
                    break

                # Reset per-depth metrics (preserve cumulative ones)
                depth_nodes_start = self.nodes_searched
                depth_terminal_start = self.terminal_nodes
                depth_pruned_start = self.pruned_nodes

                best_depth_move = None
                best_depth_score = float('-inf')

                # For single-player search, use aspiration search bounds
                initial_beta = 2.0  # Just above typical scores to enable some pruning

                # Order moves for better pruning efficiency
                ordered_moves = self._order_moves(game_state, legal_moves)

                # Evaluate each possible first move at current depth
                for move in ordered_moves:
                    try:
                        # Execute the move to get new state
                        new_state = self.move_executor.execute_move(game_state, move)

                        # Search deeper from this position with alpha-beta bounds
                        score = self._minimax(new_state, current_depth - 1, 1, best_depth_score, initial_beta)

                        # Track best move for this depth
                        if score > best_depth_score:
                            best_depth_score = score
                            best_depth_move = move

                    except Exception:
                        # Skip invalid moves
                        continue

                # Update best overall move if this depth found something better
                if best_depth_move is not None and best_depth_score > best_overall_score:
                    best_overall_score = best_depth_score
                    best_move = best_depth_move

                completed_depth = current_depth
                self.completed_depth = completed_depth  # Store for performance stats
                depth_time = time.perf_counter() - depth_start_time

                # Log per-depth completion if diagnostics enabled
                if self.diagnostics:
                    depth_nodes = self.nodes_searched - depth_nodes_start
                    depth_terminal = self.terminal_nodes - depth_terminal_start
                    depth_pruned = self.pruned_nodes - depth_pruned_start

                    self.diagnostics.logger.info(f"Depth {current_depth} completed in {depth_time:.6f}s")
                    self.diagnostics.logger.info(f"  Nodes: {depth_nodes}, Terminal: {depth_terminal}, Pruned: {depth_pruned}")
                    self.diagnostics.logger.info(f"  Best move: {best_depth_move}, Score: {best_depth_score:.3f}")

                # Check time limit after completing this depth
                total_elapsed = time.perf_counter() - search_start_time
                if total_elapsed > MAX_SEARCH_TIME_SECONDS:
                    if self.diagnostics:
                        self.diagnostics.logger.info(f"Time limit reached after depth {current_depth}")
                    break

            return best_move

        finally:
            self.search_time = time.perf_counter() - search_start_time

            # Log search completion if diagnostics enabled
            if self.diagnostics:
                # Calculate averages
                avg_depth = self.depth_sum / max(self.nodes_searched, 1)
                avg_branching_factor = self.branching_factor_sum / max(self.nodes_with_moves, 1)

                self.diagnostics.logger.info(f"Iterative deepening completed: depth {completed_depth}/{max_depth}")
                self.diagnostics.log_search_completion(
                    self.nodes_searched,
                    self.search_time,
                    self.max_depth_reached,
                    avg_depth,
                    avg_branching_factor,
                    self.cache_hits,
                    self.cache_misses,
                    len(self.transposition_table)
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

        # Check transposition table for cached result
        state_hash = hash(game_state)
        if state_hash in self.transposition_table:
            self.cache_hits += 1
            if self.diagnostics and self.diagnostics.logger.isEnabledFor(logging.DEBUG):
                self.diagnostics.logger.debug(f"Cache hit at depth {current_depth}")
            return self.transposition_table[state_hash]
        else:
            self.cache_misses += 1

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
            score = self.evaluator.evaluate(game_state)
            # Store terminal evaluation in transposition table
            self.transposition_table[state_hash] = score
            return score

        # For single-player sequential search, we want the maximum score
        # from continuing to make moves
        best_score = float('-inf')
        local_alpha = alpha

        # Order moves for better pruning efficiency
        ordered_moves = self._order_moves(game_state, legal_moves)

        for move in ordered_moves:
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
            best_score = self.evaluator.evaluate(game_state)

        # Store result in transposition table
        self.transposition_table[state_hash] = best_score

        return best_score

    def _score_move(self, game_state: GameState, move: Move, depth_from_root: int = 0) -> float:
        """
        Score a move based on heuristic evaluation, factoring in sequence potential and move depth.
        """
        card, (target_row, target_col) = move
        score = 0.0

        # Early column bonus
        if target_col == 0:
            score += 10.0
        else:
            score += max(0, 13 - target_col)

        # Sequence extension bonus
        is_sequence_building = False
        if target_col > 0:
            prev_card = game_state.board[target_row][target_col - 1]
            if prev_card and prev_card.suit == card.suit and prev_card.rank == card.rank - 1:
                is_sequence_building = True
                sequence_length = 1
                check_col = target_col - 1
                while check_col >= 0:
                    check_card = game_state.board[target_row][check_col]
                    if check_card and check_card.suit == card.suit and check_card.rank == card.rank - (target_col - check_col):
                        sequence_length += 1
                        check_col -= 1
                    else:
                        break
                score += sequence_length * 0.5

        # Suit preference (arbitrary)
        if card.suit in [0, 1]:
            score += 0.1

        # Apply discounted multiplier
        if is_sequence_building:
            decay_base = 1.5  # Tunable: try 1.3 or 1.7 if you want more/less decay
            discounted_multiplier = SEQUENCE_PREFERENCE_MULTIPLIER * (decay_base ** -depth_from_root)
            score *= discounted_multiplier

        return score

    def _order_moves(self, game_state: GameState, legal_moves: List[Move]) -> List[Move]:
        """
        Order legal moves based on heuristic evaluation.

        More promising moves are placed first to improve alpha-beta pruning efficiency.

        Args:
            game_state: Current game state
            legal_moves: List of legal moves to order

        Returns:
            List[Move]: Moves sorted by heuristic score (best first)
        """
        if not legal_moves:
            return legal_moves

        # Score each move and sort by score (descending)
        scored_moves = []
        for move in legal_moves:
            score = self._score_move(game_state, move)
            scored_moves.append((score, move))

        # Sort by score (highest first) and extract moves
        scored_moves.sort(key=lambda x: x[0], reverse=True)
        ordered_moves = [move for _, move in scored_moves]

        # Log move ordering if diagnostics enabled and debug level
        if self.diagnostics and self.diagnostics.logger.isEnabledFor(logging.DEBUG):
            self.diagnostics.logger.debug(f"Move ordering: {len(ordered_moves)} moves sorted")
            for i, (score, move) in enumerate(scored_moves[:5]):  # Log top 5 moves
                card, (target_row, target_col) = move
                self.diagnostics.logger.debug(
                    f"  {i+1}. Score {score:.1f}: {card.rank}{['♣','♠','♥','♦'][card.suit]} -> R{target_row+1}C{target_col+1}"
                )

        return ordered_moves

    def get_performance_stats(self) -> dict:
        """
        Get performance statistics from the last search.

        Returns:
            dict: Performance metrics including nodes searched, time, cache stats, etc.
        """
        total_cache_lookups = self.cache_hits + self.cache_misses
        cache_hit_rate = self.cache_hits / max(total_cache_lookups, 1)

        return {
            'nodes_searched': self.nodes_searched,
            'terminal_nodes': self.terminal_nodes,
            'pruned_nodes': self.pruned_nodes,
            'max_depth_reached': self.max_depth_reached,
            'completed_depth': self.completed_depth,  # Deepest completed iteration
            'search_time': self.search_time,
            'nodes_per_second': self.nodes_searched / max(self.search_time, 1e-9),
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'cache_hit_rate': cache_hit_rate,
            'transposition_table_size': len(self.transposition_table)
        }
