"""
Diagnostic logging system for GameState and MoveGenerator components.

This module provides comprehensive logging to debug/gamestate_diagnostics.log
including performance metrics, validation checks, and edge case handling.
"""

import logging
import time
import os
from typing import List, Set, Tuple, Optional
from dataclasses import dataclass

from .game_state import GameState, Card
from .move_gen import Move, MoveGenerator


@dataclass
class DiagnosticMetrics:
    """Container for diagnostic performance metrics."""
    initialization_time: float = 0.0
    move_generation_time: float = 0.0
    legal_move_count: int = 0
    hash_generation_time: float = 0.0
    copy_time: float = 0.0
    immutable_sequence_count: int = 0
    gap_count: int = 0


class GameStateDiagnostics:
    """Diagnostic logging for GameState operations."""
    
    def __init__(self):
        """Initialize diagnostic logger."""
        # Create debug directory if it doesn't exist
        os.makedirs("debug", exist_ok=True)
        
        # Configure logger
        self.logger = logging.getLogger("gamestate_diagnostics")
        self.logger.setLevel(logging.INFO)
        
        # Remove existing handlers to avoid duplicates
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # File handler for diagnostic output
        file_handler = logging.FileHandler("debug/gamestate_diagnostics.log", mode='a')  # Append mode
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        self.logger.info("GameState Diagnostics initialized")
    
    def log_initialization(self, state: GameState, board_config: List[Optional[Card]], metrics: DiagnosticMetrics):
        """Log GameState initialization with board configuration validation."""
        self.logger.info("=== GameState Initialization ===")
        self.logger.info(f"Board configuration: {len(board_config)} positions")
        self.logger.info(f"Initialization time: {metrics.initialization_time:.4f}s")
        
        # Validate board configuration
        card_count = sum(1 for card in board_config if card is not None)
        gap_count = len(board_config) - card_count
        self.logger.info(f"Cards on board: {card_count}, Gaps: {gap_count}")
        
        # Log immutable sequences
        immutable_positions = state.get_immutable_positions()
        self.logger.info(f"Immutable sequence positions: {len(immutable_positions)}")
        for row in range(state.ROWS):
            row_immutable = [(r, c) for (r, c) in immutable_positions if r == row]
            if row_immutable:
                self.logger.info(f"  Row {row}: {len(row_immutable)} immutable positions")
        
        # Log gaps
        gaps = state.get_gaps()
        self.logger.info(f"Gap positions: {len(gaps)}")
        for gap_row, gap_col in gaps:
            self.logger.info(f"  Gap at R{gap_row+1}C{gap_col+1}")
    
    def log_move_generation(self, state: GameState, moves: List[Move], metrics: DiagnosticMetrics):
        """Log move generation timing and legal move counts."""
        self.logger.info("=== Move Generation ===")
        self.logger.info(f"Move generation time: {metrics.move_generation_time:.4f}s")
        self.logger.info(f"Legal moves found: {len(moves)}")
        
        # Log each legal move
        for i, move in enumerate(moves):
            self.logger.info(f"  Move {i+1}: {move}")
        
        # Log gap analysis
        gaps = state.get_gaps()
        self.logger.info(f"Gap analysis: {len(gaps)} gaps on board")
        
        # Performance metrics
        if metrics.move_generation_time > 0:
            moves_per_second = len(moves) / metrics.move_generation_time
            self.logger.info(f"Move generation rate: {moves_per_second:.1f} moves/second")
    
    def log_immutable_sequence_detection(self, state: GameState):
        """Log immutable sequence detection and boundary marking."""
        self.logger.info("=== Immutable Sequence Detection ===")
        immutable_positions = state.get_immutable_positions()
        
        for row in range(state.ROWS):
            row_positions = [(r, c) for (r, c) in immutable_positions if r == row]
            if row_positions:
                # Sort by column
                row_positions.sort(key=lambda x: x[1])
                sequence_cards = []
                for _, col in row_positions:
                    card = state.get_card(row, col)
                    sequence_cards.append(str(card) if card else '--')
                
                self.logger.info(f"Row {row} immutable sequence: {' -> '.join(sequence_cards)}")
                self.logger.info(f"  Positions: {row_positions}")
                self.logger.info(f"  Boundary: columns 0-{row_positions[-1][1]} are immutable")
    
    def log_performance_metrics(self, metrics: DiagnosticMetrics, position_count: int = 1):
        """Log performance metrics for position copying and hash generation."""
        self.logger.info("=== Performance Metrics ===")
        self.logger.info(f"Hash generation time: {metrics.hash_generation_time:.4f}s")
        self.logger.info(f"Position copy time: {metrics.copy_time:.4f}s")
        
        if position_count > 1:
            total_time = metrics.initialization_time + metrics.move_generation_time + \
                        metrics.hash_generation_time + metrics.copy_time
            if total_time > 0:
                positions_per_second = position_count / total_time
                self.logger.info(f"Position evaluation rate: {positions_per_second:.1f} positions/second")
                self.logger.info(f"Target achieved: {'YES' if positions_per_second >= 1000 else 'NO'} (>1000 positions/second)")
    
    def log_edge_case_handling(self, state: GameState, move_gen: MoveGenerator):
        """Log edge case handling verification."""
        self.logger.info("=== Edge Case Handling ===")
        
        gaps = state.get_gaps()
        king_gap_count = 0
        gap_after_gap_count = 0
        first_position_gaps = 0
        
        for gap_row, gap_col in gaps:
            # Check for King gaps
            if gap_col > 0:
                left_card = state.get_card(gap_row, gap_col - 1)
                if left_card is not None and left_card.rank.value == 13:  # King
                    king_gap_count += 1
                    self.logger.info(f"King gap detected at R{gap_row+1}C{gap_col+1} (after {left_card})")
                elif left_card is None:
                    gap_after_gap_count += 1
                    self.logger.info(f"Gap-after-gap detected at R{gap_row+1}C{gap_col+1}")
            else:
                first_position_gaps += 1
                self.logger.info(f"First position gap at R{gap_row+1}C{gap_col+1}")
        
        self.logger.info(f"Edge case summary:")
        self.logger.info(f"  King gaps (unplayable): {king_gap_count}")
        self.logger.info(f"  Gap-after-gap (unplayable): {gap_after_gap_count}")
        self.logger.info(f"  First position gaps: {first_position_gaps}")
        
        # Test move generation for each gap
        for gap_row, gap_col in gaps:
            required_card = move_gen._get_required_card_for_gap(state, gap_row, gap_col)
            if required_card is None:
                self.logger.info(f"  Gap R{gap_row+1}C{gap_col+1}: No legal card (correctly handled)")
            else:
                card_pos = move_gen._find_card_position(state, required_card)
                if card_pos is None:
                    self.logger.info(f"  Gap R{gap_row+1}C{gap_col+1}: Requires {required_card} (not on board)")
                else:
                    self.logger.info(f"  Gap R{gap_row+1}C{gap_col+1}: Requires {required_card} at R{card_pos[0]+1}C{card_pos[1]+1}")


def create_diagnostics() -> GameStateDiagnostics:
    """Factory function to create diagnostics instance."""
    return GameStateDiagnostics()


def measure_performance(state: GameState, move_gen: MoveGenerator, iterations: int = 1000) -> DiagnosticMetrics:
    """Measure performance of core operations."""
    metrics = DiagnosticMetrics()
    
    # Measure hash generation
    start_time = time.time()
    for _ in range(iterations):
        _ = state.get_zobrist_hash()
    metrics.hash_generation_time = time.time() - start_time
    
    # Measure position copying
    start_time = time.time()
    for _ in range(iterations):
        _ = state.copy()
    metrics.copy_time = time.time() - start_time
    
    # Measure move generation
    start_time = time.time()
    for _ in range(iterations):
        moves = move_gen.generate_legal_moves(state)
    metrics.move_generation_time = time.time() - start_time
    metrics.legal_move_count = len(moves) if 'moves' in locals() else 0
    
    return metrics