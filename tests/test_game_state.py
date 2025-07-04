"""
Tests for simulator game state module.

These tests validate that the GameState implementation follows project principles
and provides the foundation for advanced search algorithms.
"""

import unittest
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from simulator.game_state import GameState, CardPosition


class TestCardPosition(unittest.TestCase):
    """Test CardPosition data structure"""
    
    def test_valid_card_creation(self):
        """Test creating valid card positions"""
        # Test valid ranks (2-13, Aces removed)
        for rank in range(2, 14):
            for suit in range(4):
                card = CardPosition(rank, suit)
                self.assertEqual(card.rank, rank)
                self.assertEqual(card.suit, suit)
    
    def test_invalid_rank_rejected(self):
        """Test that invalid ranks are rejected"""
        with self.assertRaises(ValueError):
            CardPosition(1, 0)  # Ace should be removed
        
        with self.assertRaises(ValueError):
            CardPosition(14, 0)  # Above King
        
        with self.assertRaises(ValueError):
            CardPosition(0, 0)  # Below 2
    
    def test_invalid_suit_rejected(self):
        """Test that invalid suits are rejected"""
        with self.assertRaises(ValueError):
            CardPosition(2, -1)  # Below 0
        
        with self.assertRaises(ValueError):
            CardPosition(2, 4)  # Above 3
    
    def test_card_immutability(self):
        """Test that CardPosition is immutable (frozen dataclass)"""
        card = CardPosition(5, 2)
        
        with self.assertRaises(Exception):
            card.rank = 6
        
        with self.assertRaises(Exception):
            card.suit = 1


class TestGameState(unittest.TestCase):
    """Test GameState implementation"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.game_state = GameState()
    
    def test_initial_state(self):
        """Test initial game state is correctly initialized"""
        # Board should be empty (all None)
        for row in range(4):
            for col in range(13):
                self.assertIsNone(self.game_state.get_card(row, col))
        
        # No gaps initially
        self.assertEqual(len(self.game_state.gaps), 0)
        
        # No immutable sequences initially
        self.assertEqual(len(self.game_state.immutable_sequences), 0)
    
    def test_valid_position_checking(self):
        """Test position validation"""
        # Valid positions
        self.assertTrue(self.game_state.is_valid_position(0, 0))
        self.assertTrue(self.game_state.is_valid_position(3, 12))
        self.assertTrue(self.game_state.is_valid_position(2, 6))
        
        # Invalid positions
        self.assertFalse(self.game_state.is_valid_position(-1, 0))
        self.assertFalse(self.game_state.is_valid_position(4, 0))
        self.assertFalse(self.game_state.is_valid_position(0, -1))
        self.assertFalse(self.game_state.is_valid_position(0, 13))
    
    def test_card_placement(self):
        """Test placing cards on the board"""
        card = CardPosition(5, 1)  # 5 of Diamonds
        
        # Should be able to place card
        result = self.game_state.place_card(card, 1, 3)
        self.assertTrue(result)
        
        # Card should be retrievable
        retrieved_card = self.game_state.get_card(1, 3)
        self.assertEqual(retrieved_card, card)
        
        # Position should not be in gaps
        self.assertNotIn((1, 3), self.game_state.gaps)
    
    def test_gap_creation(self):
        """Test creating gaps on the board"""
        # Create a gap
        result = self.game_state.create_gap(2, 5)
        self.assertTrue(result)
        
        # Position should be in gaps
        self.assertIn((2, 5), self.game_state.gaps)
        
        # Position should have no card
        self.assertIsNone(self.game_state.get_card(2, 5))
    
    def test_immutable_sequence_protection(self):
        """Test that immutable sequences cannot be modified"""
        # Mark position as immutable
        self.game_state.immutable_sequences.add((1, 2))
        
        # Should not be able to place card on immutable position
        card = CardPosition(7, 3)
        result = self.game_state.place_card(card, 1, 2)
        self.assertFalse(result)
        
        # Should not be able to create gap on immutable position
        result = self.game_state.create_gap(1, 2)
        self.assertFalse(result)
    
    def test_game_state_copying(self):
        """Test deep copying of game state for search algorithms"""
        # Set up original state
        card = CardPosition(3, 0)
        self.game_state.place_card(card, 0, 5)
        self.game_state.create_gap(2, 8)
        self.game_state.immutable_sequences.add((1, 1))
        
        # Create copy
        copy_state = self.game_state.copy()
        
        # Copy should be equal but separate
        self.assertEqual(copy_state, self.game_state)
        self.assertIsNot(copy_state, self.game_state)
        
        # Modifying copy should not affect original
        copy_state.place_card(CardPosition(4, 1), 3, 10)
        self.assertNotEqual(copy_state.get_card(3, 10), self.game_state.get_card(3, 10))
    
    def test_hash_consistency(self):
        """Test hash function for transposition tables"""
        # Same states should have same hash
        state1 = GameState()
        state2 = GameState()
        
        card = CardPosition(6, 2)
        state1.place_card(card, 1, 4)
        state2.place_card(card, 1, 4)
        
        self.assertEqual(hash(state1), hash(state2))
        
        # Different states should (likely) have different hashes
        state3 = GameState()
        state3.place_card(CardPosition(7, 2), 1, 4)
        
        self.assertNotEqual(hash(state1), hash(state3))
    
    def test_equality_comparison(self):
        """Test equality comparison for transposition tables"""
        state1 = GameState()
        state2 = GameState()
        
        # Initially equal
        self.assertEqual(state1, state2)
        
        # Add same card to both
        card = CardPosition(8, 1)
        state1.place_card(card, 2, 7)
        state2.place_card(card, 2, 7)
        
        # Still equal
        self.assertEqual(state1, state2)
        
        # Add different card to one
        state1.place_card(CardPosition(9, 1), 3, 2)
        
        # No longer equal
        self.assertNotEqual(state1, state2)
    
    def test_cache_invalidation(self):
        """Test that caches are invalidated when board changes"""
        # Initially no caches
        self.assertIsNone(self.game_state._legal_moves_cache)
        self.assertIsNone(self.game_state._evaluation_cache)
        
        # Simulate cache being set (would be done by move generator/evaluator)
        self.game_state._legal_moves_cache = []
        self.game_state._evaluation_cache = 0.5
        
        # Placing card should invalidate caches
        self.game_state.place_card(CardPosition(4, 3), 1, 6)
        self.assertIsNone(self.game_state._legal_moves_cache)
        self.assertIsNone(self.game_state._evaluation_cache)


class TestProjectAlignmentValidation(unittest.TestCase):
    """Test that GameState design validates against project principles"""
    
    def test_design_validation(self):
        """Test that GameState design validation passes"""
        try:
            from simulator.game_state import validate_game_state_design
            validate_game_state_design()
        except Exception as e:
            self.fail(f"GameState design validation failed: {e}")


if __name__ == '__main__':
    unittest.main(verbosity=2)