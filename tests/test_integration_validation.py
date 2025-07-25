"""
Integration validation test for the rule audit fixes.

This test verifies that move generation, move execution, and evaluation
all work together correctly with the new rule enforcement.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.simulator.game_state import GameState, CardPosition
from src.simulator.move_executor import MoveExecutor, InvalidMoveError
from src.simulator.evaluator import PositionEvaluator


class TestIntegrationValidation:
    """Integration tests to verify all components work together with rule fixes."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.game_state = GameState(enable_diagnostics=False)
        self.executor = MoveExecutor(enable_diagnostics=False)
        self.evaluator = PositionEvaluator(enable_performance_tracking=False, enable_diagnostics=False)
    
    def test_legal_move_generation_and_execution_consistency(self):
        """Test that all legal moves can actually be executed successfully."""
        self.setUp()
        
        # Set up a test scenario with various gap types
        # Place some cards to create interesting scenarios
        self.game_state.place_card(CardPosition(2, 0), 0, 0)  # 2C in column 1 (immutable)
        self.game_state.place_card(CardPosition(3, 0), 0, 1)  # 3C following (immutable)
        self.game_state.place_card(CardPosition(13, 1), 1, 5)  # King to create dead gap opportunity
        self.game_state.place_card(CardPosition(2, 2), 2, 3)  # 2H not in column 1 (movable)
        
        # Create gaps
        self.game_state.create_gap(1, 0)  # Gap in column 1
        self.game_state.create_gap(1, 6)  # Gap after King (should be unplayable)
        self.game_state.create_gap(2, 0)  # Another gap in column 1
        self.game_state.create_gap(3, 5)  # Regular gap
        
        # Detect immutable sequences
        self.game_state.detect_immutable_sequences()
        
        # Get legal moves
        legal_moves = self.game_state.get_legal_moves()
        
        print(f"Found {len(legal_moves)} legal moves")
        
        # Try to execute each legal move
        executed_count = 0
        for move in legal_moves:
            card, target_pos = move
            try:
                new_state = self.executor.execute_move(self.game_state, move)
                executed_count += 1
                print(f"✓ Successfully executed: {card.rank}{'CDHS'[card.suit]} -> {target_pos}")
            except InvalidMoveError as e:
                print(f"✗ FAILED to execute legal move: {card.rank}{'CDHS'[card.suit]} -> {target_pos}: {e}")
                assert False, f"Legal move should be executable: {e}"
        
        assert executed_count == len(legal_moves), f"All {len(legal_moves)} legal moves should be executable"
        print("✓ test_legal_move_generation_and_execution_consistency passed")
    
    def test_immutable_sequence_enforcement_across_components(self):
        """Test that immutable sequences are consistently enforced across all components."""
        self.setUp()
        
        # Create an immutable sequence
        self.game_state.place_card(CardPosition(2, 1), 0, 0)  # 2D in column 1
        self.game_state.place_card(CardPosition(3, 1), 0, 1)  # 3D 
        self.game_state.place_card(CardPosition(4, 1), 0, 2)  # 4D
        
        self.game_state.detect_immutable_sequences()
        
        # Verify these are detected as immutable
        assert (0, 0) in self.game_state.immutable_sequences
        assert (0, 1) in self.game_state.immutable_sequences
        assert (0, 2) in self.game_state.immutable_sequences
        
        # Create a gap where the immutable card could potentially move
        self.game_state.create_gap(1, 0)
        
        # Verify move generation doesn't suggest moving immutable cards
        legal_moves = self.game_state.get_legal_moves()
        immutable_card_moves = [
            move for move in legal_moves 
            if move[0] in [CardPosition(2, 1), CardPosition(3, 1), CardPosition(4, 1)]
        ]
        assert len(immutable_card_moves) == 0, "No legal moves should involve immutable cards"
        
        # Verify move executor rejects attempts to move immutable cards
        try:
            invalid_move = (CardPosition(2, 1), (1, 0))
            self.executor.execute_move(self.game_state, invalid_move)
            assert False, "Move executor should reject moves of immutable cards"
        except InvalidMoveError:
            pass  # Expected
        
        print("✓ test_immutable_sequence_enforcement_across_components passed")
    
    def test_gap_validation_consistency(self):
        """Test that gap validation is consistent across move generation and execution."""
        self.setUp()
        
        # Create scenarios that should produce unplayable gaps
        self.game_state.place_card(CardPosition(13, 0), 0, 5)  # King
        self.game_state.create_gap(0, 6)  # Gap after King
        
        self.game_state.create_gap(1, 3)  # First gap
        self.game_state.create_gap(1, 4)  # Gap after gap
        
        # Get legal moves
        legal_moves = self.game_state.get_legal_moves()
        
        # Verify no moves target unplayable gaps
        unplayable_gaps = [(0, 6), (1, 4)]  # Gap after King, gap after gap
        
        moves_to_unplayable = [
            move for move in legal_moves 
            if move[1] in unplayable_gaps
        ]
        
        assert len(moves_to_unplayable) == 0, f"No moves should target unplayable gaps, but found: {moves_to_unplayable}"
        
        print("✓ test_gap_validation_consistency passed")
        
    def test_evaluation_consistency_with_rules(self):
        """Test that evaluation correctly scores positions based on rule-compliant immutable sequences."""
        self.setUp()
        
        # Create a position with correctly placed immutable sequence
        correct_state = GameState(enable_diagnostics=False)
        correct_state.place_card(CardPosition(2, 0), 0, 0)  # 2C in column 1
        correct_state.place_card(CardPosition(3, 0), 0, 1)  # 3C
        correct_state.place_card(CardPosition(4, 0), 0, 2)  # 4C
        correct_state.detect_immutable_sequences()
        
        # Create a position with incorrectly placed sequence (not in column 1)
        incorrect_state = GameState(enable_diagnostics=False)
        incorrect_state.place_card(CardPosition(2, 0), 0, 1)  # 2C NOT in column 1
        incorrect_state.place_card(CardPosition(3, 0), 0, 2)  # 3C
        incorrect_state.place_card(CardPosition(4, 0), 0, 3)  # 4C
        incorrect_state.detect_immutable_sequences()
        
        # Evaluate both positions
        correct_score = self.evaluator.evaluate(correct_state)
        incorrect_score = self.evaluator.evaluate(incorrect_state)
        
        print(f"Correct sequence score: {correct_score}")
        print(f"Incorrect sequence score: {incorrect_score}")
        
        # The correctly placed sequence should score higher
        assert correct_score > incorrect_score, "Correctly placed immutable sequence should score higher"
        
        # Verify the incorrectly placed sequence has no immutable positions
        assert len(incorrect_state.immutable_sequences) == 0, "Incorrectly placed sequence should not be immutable"
        
        # Verify the correctly placed sequence has immutable positions
        assert len(correct_state.immutable_sequences) > 0, "Correctly placed sequence should be immutable"
        
        print("✓ test_evaluation_consistency_with_rules passed")
    
    def run_all_tests(self):
        """Run all integration validation tests."""
        print("Running Integration Validation Tests...")
        print("=" * 50)
        
        self.test_legal_move_generation_and_execution_consistency()
        self.test_immutable_sequence_enforcement_across_components()
        self.test_gap_validation_consistency()
        self.test_evaluation_consistency_with_rules()
        
        print("=" * 50)
        print("All Integration Validation Tests Complete!")


if __name__ == "__main__":
    test_suite = TestIntegrationValidation()
    test_suite.run_all_tests()