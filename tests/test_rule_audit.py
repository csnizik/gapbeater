"""
Comprehensive rule audit tests for GapBeater move generators and evaluators.

This module tests the specific edge cases and rule enforcement scenarios
outlined in issue #53 to ensure consistent application of game rules.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.simulator.game_state import GameState, CardPosition
from src.simulator.move_executor import MoveExecutor
from src.simulator.evaluator import PositionEvaluator


class TestRuleAudit:
    """Comprehensive tests for rule enforcement across all components."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.game_state = GameState(enable_diagnostics=False)
        self.executor = MoveExecutor(enable_diagnostics=False)
        self.evaluator = PositionEvaluator(enable_performance_tracking=False, enable_diagnostics=False)
    
    def test_gap_movement_rules_first_column(self):
        """Test that only 2s not already in column 1 can fill first column gaps."""
        self.setUp()
        
        # Create a gap in first column
        self.game_state.create_gap(0, 0)
        
        # Place a 2 in another position
        card_2h = CardPosition(2, 2)  # 2 of Hearts
        self.game_state.place_card(card_2h, 1, 5)
        
        # Place another 2 already in column 1 of a different row
        card_2c = CardPosition(2, 0)  # 2 of Clubs  
        self.game_state.place_card(card_2c, 2, 0)
        
        legal_moves = self.game_state.get_legal_moves()
        
        # Should be able to move 2H (not in column 1) to first column gap
        move_2h_to_gap = (card_2h, (0, 0))
        assert move_2h_to_gap in legal_moves, "2H not in column 1 should be able to move to first column gap"
        
        # Should NOT be able to move 2C (already in column 1) to first column gap
        move_2c_to_gap = (card_2c, (0, 0))
        assert move_2c_to_gap not in legal_moves, "2C already in column 1 should not be able to move to first column gap"
        
        print("✓ test_gap_movement_rules_first_column passed")
    
    def test_gap_movement_rules_after_king(self):
        """Test that gaps immediately to the right of Kings are unplayable."""
        self.setUp()
        
        # Place a King 
        king_spades = CardPosition(13, 3)  # King of Spades
        self.game_state.place_card(king_spades, 0, 5)
        
        # Create a gap immediately after the King
        self.game_state.create_gap(0, 6)
        
        # Place a card that would normally be able to play to that position
        # (but can't because it's after a King)
        legal_moves = self.game_state.get_legal_moves()
        
        # No moves should target the gap after the King
        gap_after_king = (0, 6)
        moves_to_dead_gap = [move for move in legal_moves if move[1] == gap_after_king]
        assert len(moves_to_dead_gap) == 0, "No moves should be allowed to gaps after Kings"
        
        print("✓ test_gap_movement_rules_after_king passed")
    
    def test_gap_movement_rules_after_gap(self):
        """Test that gaps immediately to the right of other gaps are unplayable."""
        self.setUp()
        
        # Create two adjacent gaps
        self.game_state.create_gap(0, 5)
        self.game_state.create_gap(0, 6)
        
        legal_moves = self.game_state.get_legal_moves()
        
        # No moves should target the gap that's after another gap
        gap_after_gap = (0, 6)
        moves_to_gap_after_gap = [move for move in legal_moves if move[1] == gap_after_gap]
        assert len(moves_to_gap_after_gap) == 0, "No moves should be allowed to gaps that are after other gaps"
        
        print("✓ test_gap_movement_rules_after_gap passed")
    
    def test_immutable_sequence_column_1_requirement(self):
        """Test that sequences are only immutable when starting with 2 in column 1."""
        self.setUp()
        
        # Test case 1: Sequence starting with 2 NOT in column 1 (should NOT be immutable)
        self.game_state.create_gap(0, 0)  # Gap in first position
        card_2h = CardPosition(2, 2)  # 2 of Hearts
        card_3h = CardPosition(3, 2)  # 3 of Hearts  
        card_4h = CardPosition(4, 2)  # 4 of Hearts
        
        self.game_state.place_card(card_2h, 0, 1)  # 2H in position 1 (not column 1)
        self.game_state.place_card(card_3h, 0, 2)  # 3H in position 2
        self.game_state.place_card(card_4h, 0, 3)  # 4H in position 3
        
        self.game_state.detect_immutable_sequences()
        
        # These cards should NOT be immutable since 2H is not in column 1
        assert (0, 1) not in self.game_state.immutable_sequences, "2H not in column 1 should not be immutable"
        assert (0, 2) not in self.game_state.immutable_sequences, "3H should not be immutable when sequence doesn't start in column 1"
        assert (0, 3) not in self.game_state.immutable_sequences, "4H should not be immutable when sequence doesn't start in column 1"
        
        # The 2H should still be a legal move to fill the gap in column 1
        legal_moves = self.game_state.get_legal_moves()
        move_2h_to_col1 = (card_2h, (0, 0))
        assert move_2h_to_col1 in legal_moves, "2H should be able to move to column 1 since it's not immutable"
        
        print("✓ test_immutable_sequence_column_1_requirement passed")
    
    def test_immutable_sequence_proper_detection(self):
        """Test that sequences are properly immutable when starting with 2 in column 1."""
        self.setUp()
        
        # Place a proper immutable sequence starting with 2 in column 1
        card_2s = CardPosition(2, 3)  # 2 of Spades
        card_3s = CardPosition(3, 3)  # 3 of Spades
        card_4s = CardPosition(4, 3)  # 4 of Spades
        
        self.game_state.place_card(card_2s, 1, 0)  # 2S in column 1
        self.game_state.place_card(card_3s, 1, 1)  # 3S in column 2
        self.game_state.place_card(card_4s, 1, 2)  # 4S in column 3
        
        self.game_state.detect_immutable_sequences()
        
        # These cards SHOULD be immutable since the sequence starts with 2 in column 1
        assert (1, 0) in self.game_state.immutable_sequences, "2S in column 1 should be immutable"
        assert (1, 1) in self.game_state.immutable_sequences, "3S should be immutable when part of valid sequence"
        assert (1, 2) in self.game_state.immutable_sequences, "4S should be immutable when part of valid sequence"
        
        # Create a gap to test move restrictions
        self.game_state.create_gap(0, 0)
        
        # The immutable 2S should NOT be a legal move
        legal_moves = self.game_state.get_legal_moves()
        illegal_move_2s = (card_2s, (0, 0))
        assert illegal_move_2s not in legal_moves, "Immutable 2S should not be a legal move"
        
        print("✓ test_immutable_sequence_proper_detection passed")
    
    def test_sequence_starting_higher_than_2_not_immutable(self):
        """Test that sequences starting with cards higher than 2 are not immutable."""
        self.setUp()
        
        # Place a sequence starting with 5 in column 1 (should not be immutable)
        card_5d = CardPosition(5, 1)  # 5 of Diamonds
        card_6d = CardPosition(6, 1)  # 6 of Diamonds
        card_7d = CardPosition(7, 1)  # 7 of Diamonds
        
        self.game_state.place_card(card_5d, 2, 0)  # 5D in column 1
        self.game_state.place_card(card_6d, 2, 1)  # 6D in column 2
        self.game_state.place_card(card_7d, 2, 2)  # 7D in column 3
        
        self.game_state.detect_immutable_sequences()
        
        # These cards should NOT be immutable since the sequence doesn't start with 2
        assert (2, 0) not in self.game_state.immutable_sequences, "5D should not be immutable even in column 1"
        assert (2, 1) not in self.game_state.immutable_sequences, "6D should not be immutable when sequence doesn't start with 2"
        assert (2, 2) not in self.game_state.immutable_sequences, "7D should not be immutable when sequence doesn't start with 2"
        
        print("✓ test_sequence_starting_higher_than_2_not_immutable passed")
    
    def test_debug_output_layout_examples(self):
        """Test and print debug output for the specific layout examples from the issue."""
        self.setUp()
        
        print("\n=== DEBUG OUTPUT FOR LAYOUT EXAMPLES ===")
        
        # Example 1: ["--", "2H", "3H", "4H", "5H", ...] - should NOT be immutable
        print("\nExample 1: Gap, 2H, 3H, 4H, 5H sequence")
        test_state_1 = GameState(enable_diagnostics=False)
        test_state_1.create_gap(0, 0)
        test_state_1.place_card(CardPosition(2, 2), 0, 1)  # 2H
        test_state_1.place_card(CardPosition(3, 2), 0, 2)  # 3H
        test_state_1.place_card(CardPosition(4, 2), 0, 3)  # 4H
        test_state_1.place_card(CardPosition(5, 2), 0, 4)  # 5H
        
        test_state_1.detect_immutable_sequences()
        legal_moves_1 = test_state_1.get_legal_moves()
        
        print(f"  Immutable positions: {list(test_state_1.immutable_sequences)}")
        print(f"  Legal moves count: {len(legal_moves_1)}")
        print(f"  2H can move to column 1: {(CardPosition(2, 2), (0, 0)) in legal_moves_1}")
        
        # Example 2: ["5D", "3H", "4H", "5H", "6H", ...] - should NOT be immutable
        print("\nExample 2: 5D, 3H, 4H, 5H, 6H sequence")
        test_state_2 = GameState(enable_diagnostics=False)
        test_state_2.place_card(CardPosition(5, 1), 1, 0)  # 5D in column 1
        test_state_2.place_card(CardPosition(3, 2), 1, 1)  # 3H
        test_state_2.place_card(CardPosition(4, 2), 1, 2)  # 4H
        test_state_2.place_card(CardPosition(5, 2), 1, 3)  # 5H
        test_state_2.place_card(CardPosition(6, 2), 1, 4)  # 6H
        
        test_state_2.detect_immutable_sequences()
        legal_moves_2 = test_state_2.get_legal_moves()
        
        print(f"  Immutable positions: {list(test_state_2.immutable_sequences)}")
        print(f"  Legal moves count: {len(legal_moves_2)}")
        
        # Example 3: Proper immutable sequence ["2S", "3S", "4S", "5S", ...]
        print("\nExample 3: Proper immutable sequence 2S, 3S, 4S, 5S in column 1")
        test_state_3 = GameState(enable_diagnostics=False)
        test_state_3.place_card(CardPosition(2, 3), 2, 0)  # 2S in column 1
        test_state_3.place_card(CardPosition(3, 3), 2, 1)  # 3S
        test_state_3.place_card(CardPosition(4, 3), 2, 2)  # 4S
        test_state_3.place_card(CardPosition(5, 3), 2, 3)  # 5S
        
        test_state_3.detect_immutable_sequences()
        legal_moves_3 = test_state_3.get_legal_moves()
        
        print(f"  Immutable positions: {list(test_state_3.immutable_sequences)}")
        print(f"  Legal moves count: {len(legal_moves_3)}")
        
        print("=== END DEBUG OUTPUT ===\n")
        
        print("✓ test_debug_output_layout_examples passed")
    
    def test_gap_after_gap_comprehensive(self):
        """Comprehensive test for gap-after-gap unplayability rules."""
        self.setUp()
        
        # Create multiple gap scenarios
        # Row 0: [gap, gap, 3H, ...] - second gap should be unplayable
        self.game_state.create_gap(0, 0)
        self.game_state.create_gap(0, 1)
        self.game_state.place_card(CardPosition(3, 2), 0, 2)
        
        # Row 1: [2S, gap, gap, ...] - second gap should be unplayable  
        self.game_state.place_card(CardPosition(2, 3), 1, 0)
        self.game_state.create_gap(1, 1)
        self.game_state.create_gap(1, 2)
        
        legal_moves = self.game_state.get_legal_moves()
        
        # Check that no moves target gaps that are after other gaps
        gap_after_gap_positions = [(0, 1), (1, 2)]
        for gap_pos in gap_after_gap_positions:
            moves_to_this_gap = [move for move in legal_moves if move[1] == gap_pos]
            assert len(moves_to_this_gap) == 0, f"No moves should target gap at {gap_pos} (after another gap)"
        
        print("✓ test_gap_after_gap_comprehensive passed")
    
    def run_all_tests(self):
        """Run all rule audit tests."""
        print("Running Rule Audit Tests...")
        print("=" * 50)
        
        self.test_gap_movement_rules_first_column()
        self.test_gap_movement_rules_after_king()
        self.test_gap_movement_rules_after_gap()
        self.test_immutable_sequence_column_1_requirement()
        self.test_immutable_sequence_proper_detection() 
        self.test_sequence_starting_higher_than_2_not_immutable()
        self.test_debug_output_layout_examples()
        self.test_gap_after_gap_comprehensive()
        
        print("=" * 50)
        print("All Rule Audit Tests Complete!")


if __name__ == "__main__":
    test_suite = TestRuleAudit()
    test_suite.run_all_tests()