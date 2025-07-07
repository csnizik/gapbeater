"""
Tests for undo functionality in InputHandler.collect_card_inputs
"""
import unittest
from unittest.mock import Mock, patch
import sys
import os

# Add root to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.input_handler import InputHandler
from src.layout import LayoutRenderer
from src.validator import CardValidator
from src import constants


class TestInputHandlerUndo(unittest.TestCase):
    """Test cases for undo functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.layout = LayoutRenderer()
        self.validator = CardValidator()
        self.handler = InputHandler(self.layout, self.validator)

    def test_prompt_includes_undo_after_first_card(self):
        """Test that prompt includes [U]ndo option starting from second position"""
        prompts_seen = []
        
        def mock_input(prompt):
            prompts_seen.append(prompt)
            if len(prompts_seen) <= 2:
                return ['2c', '3c'][len(prompts_seen) - 1]
            return 'z'  # Exit after checking first two prompts
        
        with patch('builtins.input', side_effect=mock_input):
            try:
                self.handler.collect_card_inputs(game_id="test_prompt_check")
            except SystemExit:
                pass
        
        # First prompt should not have undo option
        self.assertNotIn("(or [U]ndo)", prompts_seen[0])
        # Second prompt should have undo option
        self.assertIn("(or [U]ndo)", prompts_seen[1])

    def test_undo_at_first_position_does_nothing(self):
        """Test that pressing 'u' at the first position does nothing"""
        input_sequence = ['u', '2c', 'z']
        
        with patch('builtins.input', side_effect=input_sequence):
            try:
                cards = self.handler.collect_card_inputs(game_id="test_first_undo")
            except SystemExit:
                # Get saved cards 
                import json
                with open("saves/test_first_undo.json", "r") as f:
                    cards = json.load(f)
        
        # Should have 2C at first position, 'u' should have been ignored
        self.assertEqual(cards[0], '2C')
        self.assertEqual(cards[1], '')
        self.assertIn('2C', self.handler.used_cards)

    def test_undo_removes_previous_entry(self):
        """Test that undo properly removes the previous card entry"""
        input_sequence = ['2c', '3c', 'u', '4c', 'z']
        
        with patch('builtins.input', side_effect=input_sequence):
            try:
                cards = self.handler.collect_card_inputs(game_id="test_undo_removes")
            except SystemExit:
                import json
                with open("saves/test_undo_removes.json", "r") as f:
                    cards = json.load(f)
        
        # Should have 2C at [0,0] and 4C at [0,1], 3C should have been undone
        self.assertEqual(cards[0], '2C')
        self.assertEqual(cards[1], '4C')
        self.assertEqual(cards[2], '')
        
        # used_cards should contain 2C and 4C, but not 3C
        self.assertIn('2C', self.handler.used_cards)
        self.assertIn('4C', self.handler.used_cards)
        self.assertNotIn('3C', self.handler.used_cards)
        
        # Layout should match
        self.assertEqual(self.layout.grid[0][0], '2C')
        self.assertEqual(self.layout.grid[0][1], '4C')
        self.assertEqual(self.layout.grid[0][2], '  ')

    def test_undo_skips_prepopulated_cells(self):
        """Test that undo skips over prepopulated cells"""
        # Create prepopulated cards
        prepopulated = {(0, 0): '2S'}
        input_sequence = ['3s', 'u', '4s', 'z']
        
        with patch('builtins.input', side_effect=input_sequence):
            try:
                cards = self.handler.collect_card_inputs(
                    game_id="test_undo_prepop", 
                    prepopulated_cards=prepopulated
                )
            except SystemExit:
                import json
                with open("saves/test_undo_prepop.json", "r") as f:
                    cards = json.load(f)
        
        # Position [0,0] should still have prepopulated 2S
        # Position [0,1] should have 4S (after 3S was undone)
        self.assertEqual(cards[0], '2S')  # Prepopulated, unchanged
        self.assertEqual(cards[1], '4S')  # After undo and new entry
        
        # used_cards should contain the prepopulated card and final entered card
        self.assertIn('2S', self.handler.used_cards)
        self.assertIn('4S', self.handler.used_cards)
        self.assertNotIn('3S', self.handler.used_cards)

    def test_undo_handles_row_transitions(self):
        """Test that undo correctly handles undoing from first column to previous row's last column"""
        # Fill up first row with valid ranks, then add one card to second row, then undo
        first_row = [f'{rank}c' for rank in '23456789xjqk'] + ['kh']  # 12 + 1 = 13 cards for first row  
        input_sequence = first_row + ['2d', 'u', '3d', 'z']  # Fill row, add to next row, undo, add different card
        
        with patch('builtins.input', side_effect=input_sequence):
            try:
                cards = self.handler.collect_card_inputs(game_id="test_undo_row_transition")
            except SystemExit:
                import json
                with open("saves/test_undo_row_transition.json", "r") as f:
                    cards = json.load(f)
        
        # First row should be fully filled
        for i in range(13):
            self.assertNotEqual(cards[i], '')
        
        # Second row first position should have 3D (after 2D was undone)
        self.assertEqual(cards[13], '3D')
        
        # used_cards should not contain 2D but should contain 3D
        self.assertNotIn('2D', self.handler.used_cards)
        self.assertIn('3D', self.handler.used_cards)


if __name__ == '__main__':
    unittest.main()