"""
Unit tests for the MoveExecutor module.

Tests verify that the MoveExecutor correctly executes moves on GameState objects,
handles edge cases, and raises appropriate exceptions for invalid moves.
"""

import sys
import os

# Add the project root to the path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.simulator.move_executor import MoveExecutor, InvalidMoveError
from src.simulator.game_state import GameState, CardPosition


class TestMoveExecutor:
    """Test cases for MoveExecutor functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.executor = MoveExecutor()
        self.game_state = GameState()
    
    def test_execute_valid_move(self):
        """Test execution of a valid move."""
        self.setUp()
        
        # Place a card and create a gap for testing
        card_2c = CardPosition(2, 0)  # 2 of Clubs
        self.game_state.place_card(card_2c, 0, 1)
        self.game_state.create_gap(0, 0)
        
        # Execute move
        move = (card_2c, (0, 0))
        new_state = self.executor.execute_move(self.game_state, move)
        
        # Verify results
        assert new_state.get_card(0, 0) == card_2c, "Card should be at target position"
        assert new_state.get_card(0, 1) is None, "Source position should be empty"
        assert (0, 1) in new_state.gaps, "Source position should be a gap"
        assert (0, 0) not in new_state.gaps, "Target position should not be a gap"
        
        # Verify original state unchanged
        assert self.game_state.get_card(0, 1) == card_2c, "Original state should be unchanged"
        
        print("✓ test_execute_valid_move passed")
    
    def test_invalid_move_occupied_position(self):
        """Test that moving to occupied position raises InvalidMoveError."""
        self.setUp()
        
        # Place two cards
        card_2c = CardPosition(2, 0)  # 2 of Clubs
        card_3c = CardPosition(3, 0)  # 3 of Clubs
        
        self.game_state.place_card(card_2c, 0, 0)
        self.game_state.place_card(card_3c, 0, 1)
        
        # Try to move to occupied position
        move = (card_3c, (0, 0))
        try:
            self.executor.execute_move(self.game_state, move)
            assert False, "Should have raised InvalidMoveError"
        except InvalidMoveError:
            pass  # Expected
        
        print("✓ test_invalid_move_occupied_position passed")
    
    def test_invalid_move_card_not_found(self):
        """Test that moving non-existent card raises InvalidMoveError."""
        self.setUp()
        
        # Create a gap but don't place the card
        self.game_state.create_gap(0, 0)
        
        # Try to move card that's not on board
        card_2c = CardPosition(2, 0)  # 2 of Clubs - not placed
        move = (card_2c, (0, 0))
        try:
            self.executor.execute_move(self.game_state, move)
            assert False, "Should have raised InvalidMoveError"
        except InvalidMoveError:
            pass  # Expected
        
        print("✓ test_invalid_move_card_not_found passed")
    
    def test_invalid_position(self):
        """Test that moving to invalid position raises InvalidMoveError."""
        self.setUp()
        
        # Place a card
        card_2c = CardPosition(2, 0)  # 2 of Clubs
        self.game_state.place_card(card_2c, 0, 0)
        
        # Try to move to invalid position
        move = (card_2c, (5, 0))  # Row 5 is invalid
        try:
            self.executor.execute_move(self.game_state, move)
            assert False, "Should have raised InvalidMoveError"
        except InvalidMoveError:
            pass  # Expected
        
        print("✓ test_invalid_position passed")
    
    def test_immutable_sequence_protection(self):
        """Test that cards in immutable sequences cannot be moved."""
        self.setUp()
        
        # Create immutable sequence
        card_2c = CardPosition(2, 0)  # 2 of Clubs
        self.game_state.place_card(card_2c, 0, 0)  # 2 in first position
        self.game_state.detect_immutable_sequences()
        
        # Create target gap
        self.game_state.create_gap(1, 0)
        
        # Try to move card from immutable sequence
        move = (card_2c, (1, 0))
        try:
            self.executor.execute_move(self.game_state, move)
            assert False, "Should have raised InvalidMoveError"
        except InvalidMoveError:
            pass  # Expected
        
        print("✓ test_immutable_sequence_protection passed")
    
    def test_gaps_and_caches_updated(self):
        """Test that gaps are updated and caches invalidated after move."""
        self.setUp()
        
        # Set up test scenario
        card_2c = CardPosition(2, 0)  # 2 of Clubs
        self.game_state.place_card(card_2c, 0, 1)
        self.game_state.create_gap(0, 0)
        
        # Cache legal moves
        initial_moves = self.game_state.get_legal_moves()
        assert len(initial_moves) > 0, "Should have legal moves"
        
        # Execute move
        move = (card_2c, (0, 0))
        new_state = self.executor.execute_move(self.game_state, move)
        
        # Verify gaps updated correctly
        assert (0, 1) in new_state.gaps, "Source should become a gap"
        assert (0, 0) not in new_state.gaps, "Target should not be a gap"
        
        # Verify that immutable sequences are recalculated
        assert hasattr(new_state, 'immutable_sequences'), "Should have immutable sequences"
        
        print("✓ test_gaps_and_caches_updated passed")


def run_all_tests():
    """Run all test cases."""
    print("Running MoveExecutor unit tests...\n")
    
    test_instance = TestMoveExecutor()
    
    tests = [
        test_instance.test_execute_valid_move,
        test_instance.test_invalid_move_occupied_position,
        test_instance.test_invalid_move_card_not_found,
        test_instance.test_invalid_position,
        test_instance.test_immutable_sequence_protection,
        test_instance.test_gaps_and_caches_updated,
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
    sys.exit(0 if success else 1)