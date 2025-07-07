"""
Log parser module for extracting performance metrics from diagnostic logs.

Reads and normalizes key metrics from gamestate_diagnostics.log, 
move_executor_diagnostics.log, position_evaluator_diagnostics.log, 
and search_diagnostics.log files.
"""

import re
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, NamedTuple
from dataclasses import dataclass


@dataclass
class GameOutcomeMetrics:
    """Client outcome metrics for a single game run"""
    win_status: bool
    total_moves: int
    redeals_used: int
    final_placed_cards_count: int
    average_sequence_length_per_row: float
    run_duration: float  # seconds


@dataclass
class DiagnosticMetrics:
    """Aggregated diagnostic metrics from all log files"""
    gamestate_metrics: Dict[str, Any]
    move_executor_metrics: Dict[str, Any]
    position_evaluator_metrics: Dict[str, Any]
    search_metrics: Dict[str, Any]


class LogParser:
    """Parser for extracting metrics from diagnostic log files"""
    
    def __init__(self):
        self.gamestate_patterns = {
            'move_generation_time': r'Move generation: \d+ legal moves in ([\d.]+)s',
            'position_copy_time': r'Position copy time: ([\d.]+)s',
            'hash_generation_time': r'Hash generation time: ([\d.]+)s',
            'immutable_sequence_count': r'Row \d+: Found immutable sequence of (\d+) cards',
            'legal_move_count': r'Move generation: (\d+) legal moves'
        }
        
        self.move_executor_patterns = {
            'execution_time': r'Move executed: .+ in ([\d.]+)s',
            'total_moves': r'Total moves executed: (\d+)',
            'avg_execution_time': r'Average execution time: ([\d.]+)s'
        }
        
        self.position_evaluator_patterns = {
            'evaluation_time': r'Position evaluation: score=[\d.]+, time=([\d.]+)s',
            'score': r'Position evaluation: score=([\d.]+), time=',
            'correctly_placed': r'Correctly placed cards: (\d+)',
            'dead_gaps': r'dead gaps: (\d+)',
            'total_evaluations': r'Total evaluations: (\d+)'
        }
        
        self.search_patterns = {
            'search_time': r'Time taken: ([\d.]+)s',
            'positions_evaluated': r'Positions evaluated: (\d+)',
            'positions_per_second': r'Positions/second: ([\d.]+)',
            'max_depth_reached': r'Max depth reached: (\d+)',
            'avg_depth': r'Average depth reached: ([\d.]+)',
            'avg_branching_factor': r'Average branching factor: ([\d.]+)',
            'cache_hit_rate': r'Cache hit rate: ([\d.]+)%',
            'cache_hits': r'Cache hits: (\d+)',
            'cache_misses': r'Cache misses: (\d+)'
        }

    def parse_run_directory(self, run_path: Path) -> tuple[GameOutcomeMetrics, DiagnosticMetrics]:
        """
        Parse all diagnostic logs in a run directory and extract metrics.
        
        Args:
            run_path: Path to run directory (e.g., debug/123456789)
            
        Returns:
            Tuple of (outcome_metrics, diagnostic_metrics)
        """
        if not run_path.exists():
            raise FileNotFoundError(f"Run directory not found: {run_path}")
            
        # Load manifest for run metadata
        manifest_path = run_path / "manifest.json"
        manifest = {}
        if manifest_path.exists():
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
        
        # Parse each diagnostic log file
        gamestate_metrics = self._parse_gamestate_log(run_path / "gamestate_diagnostics.log")
        move_executor_metrics = self._parse_move_executor_log(run_path / "move_executor_diagnostics.log")
        position_evaluator_metrics = self._parse_position_evaluator_log(run_path / "position_evaluator_diagnostics.log")
        search_metrics = self._parse_search_log(run_path / "search_diagnostics.log")
        
        # Calculate outcome metrics
        outcome_metrics = self._calculate_outcome_metrics(
            gamestate_metrics, move_executor_metrics, 
            position_evaluator_metrics, search_metrics, manifest
        )
        
        diagnostic_metrics = DiagnosticMetrics(
            gamestate_metrics=gamestate_metrics,
            move_executor_metrics=move_executor_metrics,
            position_evaluator_metrics=position_evaluator_metrics,
            search_metrics=search_metrics
        )
        
        return outcome_metrics, diagnostic_metrics

    def _parse_log_file(self, log_path: Path, patterns: Dict[str, str]) -> Dict[str, Any]:
        """Parse a log file using provided regex patterns"""
        if not log_path.exists():
            return {}
            
        metrics = {}
        with open(log_path, 'r') as f:
            content = f.read()
            
        for metric_name, pattern in patterns.items():
            matches = re.findall(pattern, content)
            if matches:
                if metric_name in ['total_moves', 'total_evaluations', 'positions_evaluated', 
                                 'max_depth_reached', 'cache_hits', 'cache_misses', 'correctly_placed', 
                                 'dead_gaps', 'legal_move_count', 'immutable_sequence_count']:
                    # Integer metrics
                    metrics[metric_name] = [int(m) for m in matches]
                else:
                    # Float metrics  
                    metrics[metric_name] = [float(m) for m in matches]
            else:
                metrics[metric_name] = []
                
        return metrics

    def _parse_gamestate_log(self, log_path: Path) -> Dict[str, Any]:
        """Parse gamestate_diagnostics.log"""
        return self._parse_log_file(log_path, self.gamestate_patterns)

    def _parse_move_executor_log(self, log_path: Path) -> Dict[str, Any]:
        """Parse move_executor_diagnostics.log"""
        return self._parse_log_file(log_path, self.move_executor_patterns)

    def _parse_position_evaluator_log(self, log_path: Path) -> Dict[str, Any]:
        """Parse position_evaluator_diagnostics.log"""
        return self._parse_log_file(log_path, self.position_evaluator_patterns)

    def _parse_search_log(self, log_path: Path) -> Dict[str, Any]:
        """Parse search_diagnostics.log"""
        return self._parse_log_file(log_path, self.search_patterns)

    def _calculate_outcome_metrics(self, gamestate_metrics: Dict, move_executor_metrics: Dict,
                                 position_evaluator_metrics: Dict, search_metrics: Dict,
                                 manifest: Dict) -> GameOutcomeMetrics:
        """Calculate client outcome metrics from parsed diagnostic data"""
        
        # Extract total moves from move executor
        total_moves = 0
        if move_executor_metrics.get('total_moves'):
            total_moves = max(move_executor_metrics['total_moves'])
        
        # Calculate redeals used (estimate based on search phases)
        redeals_used = 0
        if search_metrics.get('search_time'):
            # Estimate redeals as number of distinct search phases
            redeals_used = len(search_metrics['search_time']) - 1
            
        # Calculate final placed cards from position evaluator
        final_placed_cards_count = 0
        if position_evaluator_metrics.get('correctly_placed'):
            final_placed_cards_count = max(position_evaluator_metrics['correctly_placed']) if position_evaluator_metrics['correctly_placed'] else 0
            
        # Calculate average sequence length per row
        avg_sequence_length = 0.0
        if gamestate_metrics.get('immutable_sequence_count'):
            sequences = gamestate_metrics['immutable_sequence_count']
            avg_sequence_length = sum(sequences) / 4.0 if sequences else 0.0  # 4 rows
            
        # Determine win status (simplified: win if no dead gaps and high placement)
        win_status = False
        if position_evaluator_metrics.get('dead_gaps'):
            last_dead_gaps = position_evaluator_metrics['dead_gaps'][-1] if position_evaluator_metrics['dead_gaps'] else 0
            win_status = (last_dead_gaps == 0 and final_placed_cards_count >= 48)  # Near complete
            
        # Calculate run duration
        run_duration = 0.0
        if search_metrics.get('search_time'):
            run_duration = sum(search_metrics['search_time'])
            
        return GameOutcomeMetrics(
            win_status=win_status,
            total_moves=total_moves,
            redeals_used=redeals_used,
            final_placed_cards_count=final_placed_cards_count,
            average_sequence_length_per_row=avg_sequence_length,
            run_duration=run_duration
        )

    def parse_multiple_runs(self, debug_path: Path, game_id: str) -> List[tuple[GameOutcomeMetrics, DiagnosticMetrics]]:
        """
        Parse multiple runs for the same game ID.
        
        Args:
            debug_path: Path to debug directory
            game_id: Game ID to analyze
            
        Returns:
            List of (outcome_metrics, diagnostic_metrics) tuples for each run
        """
        runs = []
        game_dir = debug_path / game_id
        
        if not game_dir.exists():
            return runs
            
        # Look for sub-subdirectories (multiple runs)
        for run_dir in game_dir.iterdir():
            if run_dir.is_dir():
                try:
                    outcome, diagnostic = self.parse_run_directory(run_dir)
                    runs.append((outcome, diagnostic))
                except Exception as e:
                    print(f"Warning: Failed to parse run {run_dir}: {e}")
                    
        # If no sub-subdirectories, parse the game_dir itself as a single run
        if not runs:
            try:
                outcome, diagnostic = self.parse_run_directory(game_dir)
                runs.append((outcome, diagnostic))
            except Exception as e:
                print(f"Warning: Failed to parse run {game_dir}: {e}")
                
        return runs