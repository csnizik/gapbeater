#!/usr/bin/env python3
"""
Unit tests for incremental reshuffle analysis functionality
"""
import unittest
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.game import GameManager
from src.layout import LayoutRenderer
from src.input_handler import InputHandler
from src.validator import CardValidator
from src.simulator.game_state import GameState


class TestIncrementalReshuffleFlow(unittest.TestCase):
    """Test cases for incremental reshuffle analysis flow"""

    def setUp(self):
        """Set up test fixtures"""
        self.manager = GameManager()
        self.layout = LayoutRenderer()
        self.validator = CardValidator()
        self.handler = InputHandler(self.layout, self.validator)

    def test_move_display_format(self):
        """Test that moves are displayed in the correct format (6H -> R2C12)"""
        # Create a test board with a legal move
        test_board = ["2C", "3C", "--", "5C", "6C", "--", "--", "--", "--", "--", "--", "--", "--",
                      "--", "4C", "2D", "3D", "--", "--", "--", "--", "--", "--", "--", "--", "--",
                      "2H", "3H", "4H", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--",
                      "2S", "3S", "4S", "5S", "--", "--", "--", "--", "--", "--", "--", "--", "--"]
        
        self.manager.current_game[0] = test_board
        
        game_state = GameState(enable_diagnostics=False)
        self.assertTrue(game_state.load_from_flat_board(test_board))
        
        # Test that _analyze_and_display_moves returns False (not won) and has moves
        is_won = self.manager._analyze_and_display_moves(game_state, "Test phase")
        self.assertFalse(is_won)
        
        # Verify there are legal moves
        legal_moves = game_state.get_legal_moves()
        self.assertGreater(len(legal_moves), 0)
        
        # Verify move format by checking a specific move
        for card, (target_row, target_col) in legal_moves:
            # Should be able to move 4C to row 0, col 2 (R1C3)
            if card.rank == 4 and card.suit == 0:  # 4 of Clubs
                self.assertEqual(target_row, 0)
                self.assertEqual(target_col, 2)
                break
        else:
            self.fail("Expected 4C -> R1C3 move not found")

    def test_win_condition_detection(self):
        """Test that win condition is properly detected"""
        # Create a winning board (no gaps)
        winning_board = []
        suits = ['C', 'D', 'H', 'S']
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', 'X', 'J', 'Q', 'K', '2']
        
        for row in range(4):
            for col in range(13):
                suit = suits[row]
                rank = ranks[col]
                winning_board.append(f"{rank}{suit}")
        
        self.manager.current_game[0] = winning_board
        
        game_state = GameState(enable_diagnostics=False)
        self.assertTrue(game_state.load_from_flat_board(winning_board))
        
        # Verify no gaps
        self.assertEqual(len(game_state.gaps), 0)
        
        # Test that _analyze_and_display_moves returns True (game won)
        is_won = self.manager._analyze_and_display_moves(game_state, "Win test")
        self.assertTrue(is_won)

    def test_reshuffle_number_tracking(self):
        """Test that reshuffle numbers are tracked correctly"""
        # Test initial state (no reshuffle)
        self.assertIsNone(self.handler.current_reshuffle)
        self.assertIsNone(self.layout.reshuffle_number)
        
        # Test setting reshuffle number
        self.handler.current_reshuffle = 1
        self.layout.set_reshuffle_number(1)
        
        self.assertEqual(self.handler.current_reshuffle, 1)
        self.assertEqual(self.layout.reshuffle_number, 1)
        
        # Test resetting
        self.handler.current_reshuffle = None
        self.layout.set_reshuffle_number(None)
        
        self.assertIsNone(self.handler.current_reshuffle)
        self.assertIsNone(self.layout.reshuffle_number)

    def test_compute_prepopulated_cells(self):
        """Test that prepopulated cells are computed correctly from immutable sequences"""
        # Create a board with some immutable sequences
        test_board = ["2C", "3C", "4C", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--",
                      "2D", "3D", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--",
                      "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--",
                      "2S", "3S", "4S", "5S", "--", "--", "--", "--", "--", "--", "--", "--", "--"]
        
        skip_cells, prepopulated = self.manager.compute_prepopulated_cells(test_board)
        
        # Should skip cells that are part of immutable sequences starting with 2
        self.assertIn((0, 0), skip_cells)  # 2C
        self.assertIn((0, 1), skip_cells)  # 3C  
        self.assertIn((0, 2), skip_cells)  # 4C
        self.assertIn((1, 0), skip_cells)  # 2D
        self.assertIn((1, 1), skip_cells)  # 3D
        self.assertIn((3, 0), skip_cells)  # 2S
        self.assertIn((3, 1), skip_cells)  # 3S
        self.assertIn((3, 2), skip_cells)  # 4S
        self.assertIn((3, 3), skip_cells)  # 5S
        
        # Check prepopulated cards
        self.assertEqual(prepopulated[(0, 0)], "2C")
        self.assertEqual(prepopulated[(0, 1)], "3C")
        self.assertEqual(prepopulated[(0, 2)], "4C")

    def test_move_sequence_grouping(self):
        """Test that move sequences are grouped into rows of three"""
        import io
        from contextlib import redirect_stdout
        
        # Test short sequence (≤3 moves) - should stay on single line
        test_board = ["2C", "3C", "--", "5C", "6C", "--", "--", "--", "--", "--", "--", "--", "--",
                      "--", "4C", "2D", "3D", "--", "--", "--", "--", "--", "--", "--", "--", "--",
                      "2H", "3H", "4H", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--",
                      "2S", "3S", "4S", "5S", "--", "--", "--", "--", "--", "--", "--", "--", "--"]
        
        self.manager.current_game = [test_board]
        game_state = GameState(enable_diagnostics=False)
        self.assertTrue(game_state.load_from_flat_board(test_board))
        
        # Capture output to verify formatting
        captured_output = io.StringIO()
        with redirect_stdout(captured_output):
            is_won = self.manager._analyze_and_display_moves(game_state, "Test grouping")
        
        output = captured_output.getvalue()
        
        # Should not be won and should have moves
        self.assertFalse(is_won)
        
        # Verify the output format - should have header and move line(s)
        lines = output.strip().split('\n')
        self.assertGreater(len(lines), 0)
        
        # First line should be the header
        self.assertIn("Test grouping: Optimal move sequence:", lines[0])
        
        # Move lines should contain "->" 
        move_lines = [line for line in lines if '->' in line]
        self.assertGreater(len(move_lines), 0)
        
        # For this test case, we expect a small number of moves (likely 1)
        # Each line should have at most 3 moves (separated by ", ")
        for line in move_lines:
            moves_in_line = line.count('->')
            self.assertLessEqual(moves_in_line, 3, f"Line has {moves_in_line} moves, should be ≤3: {line}")
            
            # Verify comma separation if multiple moves
            if moves_in_line > 1:
                # Should have (moves_in_line - 1) commas between moves
                expected_commas = moves_in_line - 1
                actual_commas = line.count(', ')
                self.assertEqual(actual_commas, expected_commas, 
                               f"Expected {expected_commas} commas for {moves_in_line} moves, got {actual_commas}")


if __name__ == '__main__':
    print("Running incremental reshuffle tests...")
    unittest.main(verbosity=2)