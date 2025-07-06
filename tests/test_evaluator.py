"""
Unit tests for position evaluator functionality.

Tests verify scoring logic for correctly placed cards and gap quality assessment.
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.simulator.game_state import GameState, CardPosition
from src.simulator.evaluator import PositionEvaluator


class TestPositionEvaluator:
    """Test cases for PositionEvaluator functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.evaluator = PositionEvaluator()
        self.game_state = GameState(enable_diagnostics=False)

    def test_empty_board_evaluation(self):
        """Test evaluation of empty board returns base score."""
        self.setUp()
        
        score = self.evaluator.evaluate(self.game_state)
        
        # Empty board should have base score normalized
        expected_normalized = (self.evaluator.BASE_SCORE / 
                             (self.evaluator.BASE_SCORE + 52 * self.evaluator.CORRECT_PLACEMENT_WEIGHT)) * 100
        
        assert abs(score - expected_normalized) < 0.01, f"Expected {expected_normalized}, got {score}"
        print("✓ test_empty_board_evaluation passed")

    def test_correct_placements_scoring(self):
        """Test that correctly placed cards increase score."""
        self.setUp()
        
        # Create immutable sequence: 2C, 3C in first row
        card_2c = CardPosition(2, 0)  # 2 of Clubs
        card_3c = CardPosition(3, 0)  # 3 of Clubs
        
        self.game_state.place_card(card_2c, 0, 0)  # Place 2C in first position
        self.game_state.place_card(card_3c, 0, 1)  # Place 3C next to it
        self.game_state.detect_immutable_sequences()
        
        score = self.evaluator.evaluate(self.game_state)
        
        # Should have higher score than empty board due to correct placements
        empty_score = (self.evaluator.BASE_SCORE / 
                      (self.evaluator.BASE_SCORE + 52 * self.evaluator.CORRECT_PLACEMENT_WEIGHT)) * 100
        
        assert score > empty_score, f"Score {score} should be higher than empty board {empty_score}"
        print("✓ test_correct_placements_scoring passed")

    def test_dead_gap_penalty(self):
        """Test that gaps after Kings result in lower scores."""
        self.setUp()
        
        # Place a King in the board
        king_hearts = CardPosition(13, 2)  # King of Hearts
        self.game_state.place_card(king_hearts, 0, 5)
        
        # Create a gap immediately after the King
        self.game_state.create_gap(0, 6)
        
        score_with_dead_gap = self.evaluator.evaluate(self.game_state)
        
        # Compare with board that has King but no gap after it
        clean_state = GameState(enable_diagnostics=False)
        clean_state.place_card(king_hearts, 0, 5)
        score_without_dead_gap = self.evaluator.evaluate(clean_state)
        
        assert score_with_dead_gap < score_without_dead_gap, \
            f"Dead gap score {score_with_dead_gap} should be lower than clean {score_without_dead_gap}"
        print("✓ test_dead_gap_penalty passed")

    def test_normalized_score_range(self):
        """Test that evaluation returns scores in 0-100 range."""
        self.setUp()
        
        # Test various board states
        test_states = []
        
        # Empty board
        test_states.append(GameState(enable_diagnostics=False))
        
        # Board with some correct placements
        state_with_placements = GameState(enable_diagnostics=False)
        for i in range(4):
            card = CardPosition(2, i)  # 2s of different suits
            state_with_placements.place_card(card, i, 0)
        state_with_placements.detect_immutable_sequences()
        test_states.append(state_with_placements)
        
        # Board with dead gaps
        state_with_dead_gaps = GameState(enable_diagnostics=False)
        for i in range(4):
            king = CardPosition(13, i)  # Kings of different suits
            state_with_dead_gaps.place_card(king, i, 5)
            state_with_dead_gaps.create_gap(i, 6)
        test_states.append(state_with_dead_gaps)
        
        for state in test_states:
            score = self.evaluator.evaluate(state)
            assert 0.0 <= score <= 100.0, f"Score {score} is outside 0-100 range"
        
        print("✓ test_normalized_score_range passed")

    def test_evaluation_performance(self):
        """Test that evaluation completes efficiently."""
        self.setUp()
        
        # Create a complex board state
        complex_state = GameState(enable_diagnostics=False)
        
        # Add some cards and gaps
        cards_to_place = [
            (CardPosition(2, 0), 0, 0),
            (CardPosition(3, 0), 0, 1),
            (CardPosition(4, 0), 0, 2),
            (CardPosition(13, 1), 1, 8),
            (CardPosition(13, 2), 2, 10),
        ]
        
        for card, row, col in cards_to_place:
            complex_state.place_card(card, row, col)
        
        # Create some gaps including dead ones
        complex_state.create_gap(1, 9)  # Dead gap after King
        complex_state.create_gap(2, 11)  # Dead gap after King
        complex_state.create_gap(3, 5)   # Regular gap
        
        complex_state.detect_immutable_sequences()
        
        # Evaluate multiple times to test performance
        import time
        start_time = time.perf_counter()
        
        for _ in range(1000):
            score = self.evaluator.evaluate(complex_state)
        
        end_time = time.perf_counter()
        avg_time = (end_time - start_time) / 1000
        
        # Should complete very quickly (target: 50,000+ positions/second = <0.00002s each)
        assert avg_time < 0.001, f"Average evaluation time {avg_time}s is too slow"
        
        # Verify score is reasonable
        assert 0.0 <= score <= 100.0, f"Score {score} is outside valid range"
        
        print(f"✓ test_evaluation_performance passed (avg: {avg_time:.6f}s per evaluation)")

    def test_performance_stats(self):
        """Test that performance statistics are tracked correctly."""
        self.setUp()
        
        # Perform some evaluations
        state = GameState(enable_diagnostics=False)
        for _ in range(10):
            self.evaluator.evaluate(state)
        
        stats = self.evaluator.get_performance_stats()
        
        assert stats['evaluation_count'] == 10, "Should track evaluation count"
        assert stats['total_time'] > 0, "Should track total time"
        assert stats['average_time'] > 0, "Should calculate average time"
        assert stats['evaluations_per_second'] > 0, "Should calculate evaluations per second"
        
        print("✓ test_performance_stats passed")


def run_all_tests():
    """Run all evaluator tests."""
    print("Running PositionEvaluator unit tests...\n")
    
    test_instance = TestPositionEvaluator()
    tests = [
        test_instance.test_empty_board_evaluation,
        test_instance.test_correct_placements_scoring,
        test_instance.test_dead_gap_penalty,
        test_instance.test_normalized_score_range,
        test_instance.test_evaluation_performance,
        test_instance.test_performance_stats,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ {test.__name__} failed: {e}")
    
    print(f"\nTest Results: {passed}/{total} tests passed")
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)