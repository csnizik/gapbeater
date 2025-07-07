"""
Unit tests for log parser and correlation engine functionality.

Tests verify parsing logic for diagnostic logs and metric extraction.
"""

import sys
import os
import unittest
import tempfile
import json
from pathlib import Path

# Add src to path for imports  
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.log_parser import LogParser, GameOutcomeMetrics, DiagnosticMetrics
from analysis.correlation_engine import CorrelationEngine


class TestLogParser(unittest.TestCase):
    """Test cases for LogParser functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.parser = LogParser()
        self.temp_dir = tempfile.mkdtemp()
        self.run_path = Path(self.temp_dir) / "test-run"
        self.run_path.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def create_sample_logs(self):
        """Create sample log files for testing."""
        
        # Create manifest
        manifest = {
            "run_metadata": {
                "timestamp": "2025-01-01T00:00:00.000000",
                "run_id": "test-run",
                "format_version": "1.0"
            },
            "game_session": {
                "game_id": "test-game",
                "session_start": "2025-01-01T00:00:00.000000"
            }
        }
        with open(self.run_path / "manifest.json", 'w') as f:
            json.dump(manifest, f)

        # Create gamestate log
        gamestate_log = """2025-01-01 00:00:01,100 - INFO - Move generation: 10 legal moves in 0.001500s
2025-01-01 00:00:02,200 - INFO - Row 0: Found immutable sequence of 5 cards
2025-01-01 00:00:03,300 - DEBUG - Position copy time: 0.000100s
2025-01-01 00:00:04,400 - DEBUG - Hash generation time: 0.000050s"""
        
        with open(self.run_path / "gamestate_diagnostics.log", 'w') as f:
            f.write(gamestate_log)

        # Create move executor log
        move_executor_log = """2025-01-01 00:00:01,150 - INFO - Move executed: 2H -> (0, 1) in 0.000200s
2025-01-01 00:00:02,250 - INFO - Total moves executed: 3
2025-01-01 00:00:03,350 - INFO - Average execution time: 0.000190s"""
        
        with open(self.run_path / "move_executor_diagnostics.log", 'w') as f:
            f.write(move_executor_log)

        # Create position evaluator log
        position_evaluator_log = """2025-01-01 00:00:01,120 - INFO - Position evaluation: score=125.50, time=0.0015s
2025-01-01 00:00:01,120 - DEBUG - Correctly placed cards: 25, dead gaps: 1
2025-01-01 00:00:02,220 - INFO - Total evaluations: 2"""
        
        with open(self.run_path / "position_evaluator_diagnostics.log", 'w') as f:
            f.write(position_evaluator_log)

        # Create search log
        search_log = """2025-01-01 00:00:01,000 - INFO - Positions evaluated: 15000
2025-01-01 00:00:01,000 - INFO - Time taken: 2.500000s
2025-01-01 00:00:01,000 - INFO - Positions/second: 6000.00
2025-01-01 00:00:01,000 - INFO - Max depth reached: 8
2025-01-01 00:00:01,000 - INFO - Average depth reached: 6.50
2025-01-01 00:00:01,000 - INFO - Average branching factor: 9.2
2025-01-01 00:00:01,000 - INFO - Cache hits: 1200
2025-01-01 00:00:01,000 - INFO - Cache misses: 800
2025-01-01 00:00:01,000 - INFO - Cache hit rate: 60.0%"""
        
        with open(self.run_path / "search_diagnostics.log", 'w') as f:
            f.write(search_log)

    def test_parse_gamestate_log(self):
        """Test parsing of gamestate diagnostic log."""
        self.create_sample_logs()
        
        metrics = self.parser._parse_gamestate_log(self.run_path / "gamestate_diagnostics.log")
        
        self.assertIn('legal_move_count', metrics)
        self.assertEqual(metrics['legal_move_count'], [10])
        self.assertIn('move_generation_time', metrics)
        self.assertEqual(metrics['move_generation_time'], [0.001500])
        self.assertIn('immutable_sequence_count', metrics)
        self.assertEqual(metrics['immutable_sequence_count'], [5])

    def test_parse_move_executor_log(self):
        """Test parsing of move executor diagnostic log."""
        self.create_sample_logs()
        
        metrics = self.parser._parse_move_executor_log(self.run_path / "move_executor_diagnostics.log")
        
        self.assertIn('execution_time', metrics)
        self.assertEqual(metrics['execution_time'], [0.000200])
        self.assertIn('total_moves', metrics)
        self.assertEqual(metrics['total_moves'], [3])

    def test_parse_position_evaluator_log(self):
        """Test parsing of position evaluator diagnostic log."""
        self.create_sample_logs()
        
        metrics = self.parser._parse_position_evaluator_log(self.run_path / "position_evaluator_diagnostics.log")
        
        self.assertIn('score', metrics)
        self.assertEqual(metrics['score'], [125.50])
        self.assertIn('correctly_placed', metrics)
        self.assertEqual(metrics['correctly_placed'], [25])
        self.assertIn('dead_gaps', metrics)
        self.assertEqual(metrics['dead_gaps'], [1])

    def test_parse_search_log(self):
        """Test parsing of search diagnostic log."""
        self.create_sample_logs()
        
        metrics = self.parser._parse_search_log(self.run_path / "search_diagnostics.log")
        
        self.assertIn('positions_evaluated', metrics)
        self.assertEqual(metrics['positions_evaluated'], [15000])
        self.assertIn('search_time', metrics)
        self.assertEqual(metrics['search_time'], [2.500000])
        self.assertIn('cache_hit_rate', metrics)
        self.assertEqual(metrics['cache_hit_rate'], [60.0])

    def test_parse_run_directory(self):
        """Test parsing complete run directory."""
        self.create_sample_logs()
        
        outcome, diagnostic = self.parser.parse_run_directory(self.run_path)
        
        # Check outcome metrics
        self.assertIsInstance(outcome, GameOutcomeMetrics)
        self.assertEqual(outcome.total_moves, 3)
        self.assertEqual(outcome.final_placed_cards_count, 25)
        self.assertAlmostEqual(outcome.average_sequence_length_per_row, 1.25)  # 5/4 rows
        
        # Check diagnostic metrics
        self.assertIsInstance(diagnostic, DiagnosticMetrics)
        self.assertIn('legal_move_count', diagnostic.gamestate_metrics)
        self.assertIn('total_moves', diagnostic.move_executor_metrics)

    def test_outcome_metric_calculation(self):
        """Test calculation of outcome metrics from diagnostic data."""
        self.create_sample_logs()
        
        outcome, _ = self.parser.parse_run_directory(self.run_path)
        
        # Test win status determination (should be False for this simple case)
        self.assertFalse(outcome.win_status)
        
        # Test redeals calculation (based on search phases)
        self.assertEqual(outcome.redeals_used, 0)  # Single search phase
        
        # Test run duration
        self.assertAlmostEqual(outcome.run_duration, 2.5)


class TestCorrelationEngine(unittest.TestCase):
    """Test cases for CorrelationEngine functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.engine = CorrelationEngine()
        self.temp_dir = tempfile.mkdtemp()
        self.debug_path = Path(self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def create_sample_run(self, game_id: str, run_id: str, win_status: bool = False):
        """Create a sample run directory with logs."""
        run_path = self.debug_path / game_id / run_id
        run_path.mkdir(parents=True, exist_ok=True)
        
        # Create basic logs
        manifest = {
            "run_metadata": {"timestamp": "2025-01-01T00:00:00.000000", "run_id": run_id},
            "game_session": {"game_id": game_id}
        }
        with open(run_path / "manifest.json", 'w') as f:
            json.dump(manifest, f)
            
        # Adjust scores based on win status
        score = 225.0 if win_status else 125.0
        placed_cards = 48 if win_status else 25
        dead_gaps = 0 if win_status else 2
        
        logs = {
            "gamestate_diagnostics.log": f"2025-01-01 00:00:01,100 - INFO - Move generation: 10 legal moves in 0.001500s\n2025-01-01 00:00:02,200 - INFO - Row 0: Found immutable sequence of 5 cards",
            "move_executor_diagnostics.log": f"2025-01-01 00:00:01,150 - INFO - Move executed: 2H -> (0, 1) in 0.000200s\n2025-01-01 00:00:02,250 - INFO - Total moves executed: 3",
            "position_evaluator_diagnostics.log": f"2025-01-01 00:00:01,120 - INFO - Position evaluation: score={score}, time=0.0015s\n2025-01-01 00:00:01,120 - DEBUG - Correctly placed cards: {placed_cards}, dead gaps: {dead_gaps}",
            "search_diagnostics.log": f"2025-01-01 00:00:01,000 - INFO - Positions evaluated: 15000\n2025-01-01 00:00:01,000 - INFO - Time taken: 2.500000s\n2025-01-01 00:00:01,000 - INFO - Positions/second: 6000.00"
        }
        
        for filename, content in logs.items():
            with open(run_path / filename, 'w') as f:
                f.write(content)

    def test_single_run_analysis(self):
        """Test analysis of a single run."""
        self.create_sample_run("test-game", "run1")
        
        report = self.engine.analyze_single_run(self.debug_path, "test-game")
        
        self.assertEqual(report.game_id, "test-game")
        self.assertEqual(report.run_count, 1)
        self.assertIn("win_status", report.outcome_summary)
        self.assertIn("gamestate", report.diagnostic_summary)
        self.assertEqual(len(report.correlations), 0)  # No correlations for single run
        self.assertEqual(len(report.comparisons), 0)   # No comparisons for single run

    def test_multiple_run_analysis(self):
        """Test analysis of multiple runs with comparisons."""
        self.create_sample_run("test-game", "run1", win_status=False)
        self.create_sample_run("test-game", "run2", win_status=True)
        
        report = self.engine.analyze_multiple_runs(self.debug_path, "test-game")
        
        self.assertEqual(report.game_id, "test-game")
        self.assertEqual(report.run_count, 2)
        self.assertIn("win_rate", report.outcome_summary)
        self.assertEqual(report.outcome_summary["win_rate"], 0.5)  # 1 win out of 2
        self.assertEqual(len(report.comparisons), 1)  # One pairwise comparison

    def test_metric_aggregation(self):
        """Test aggregation of metrics across multiple runs."""
        self.create_sample_run("test-game", "run1", win_status=False)
        self.create_sample_run("test-game", "run2", win_status=True)
        
        report = self.engine.analyze_multiple_runs(self.debug_path, "test-game")
        
        # Check aggregated outcome metrics
        self.assertIn("avg_final_placed_cards", report.outcome_summary)
        self.assertAlmostEqual(report.outcome_summary["avg_final_placed_cards"], 36.5)  # (25+48)/2
        
        # Check diagnostic summary structure
        self.assertIn("gamestate", report.diagnostic_summary)
        self.assertIn("position_evaluator", report.diagnostic_summary)

    def test_run_comparison(self):
        """Test generation of run comparisons."""
        self.create_sample_run("test-game", "run1", win_status=False)
        self.create_sample_run("test-game", "run2", win_status=True)
        
        report = self.engine.analyze_multiple_runs(self.debug_path, "test-game")
        
        self.assertEqual(len(report.comparisons), 1)
        comparison = report.comparisons[0]
        
        self.assertEqual(comparison.run1_id, "run_1")
        self.assertEqual(comparison.run2_id, "run_2")
        self.assertIn("final_placed_cards", comparison.outcome_differences)
        self.assertIn("win_status_change", comparison.outcome_differences)

    def test_recommendation_generation(self):
        """Test generation of recommendations based on analysis."""
        self.create_sample_run("test-game", "run1", win_status=False)
        
        report = self.engine.analyze_single_run(self.debug_path, "test-game")
        
        self.assertIsInstance(report.recommendations, list)
        self.assertGreater(len(report.recommendations), 0)

    def test_nonexistent_run(self):
        """Test handling of nonexistent run directory."""
        report = self.engine.analyze_single_run(self.debug_path, "nonexistent-game")
        
        self.assertEqual(report.game_id, "nonexistent-game")
        self.assertEqual(report.run_count, 0)
        self.assertIn("No valid runs found", report.recommendations[0])


if __name__ == '__main__':
    unittest.main()