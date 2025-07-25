"""
Test to verify that move simulation continues until there are 4 legitimate gaps
(gaps that are to the right of either a King or another gap).

This addresses the specific requirement from issue #53:
"No simulated set of moves stops being generated until there are 4 legitimate gaps"
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.simulator.game_state import GameState, CardPosition


class TestMoveSimulationLimits:
    """Test move simulation stopping conditions."""
    
    def test_move_generation_stops_only_at_4_legitimate_gaps(self):
        """Test that moves are generated until all 4 gaps are legitimately unplayable."""
        game_state = GameState(enable_diagnostics=False)
        
        # Scenario 1: Less than 4 legitimate gaps - should have legal moves
        print("=== Scenario 1: 2 legitimate gaps ===")
        
        # Create 2 gaps after Kings (legitimate/unplayable)
        game_state.place_card(CardPosition(13, 0), 0, 5)  # King
        game_state.create_gap(0, 6)  # Gap after King (legitimate)
        
        game_state.place_card(CardPosition(13, 1), 1, 7)  # King  
        game_state.create_gap(1, 8)  # Gap after King (legitimate)
        
        # Create 2 playable gaps
        game_state.place_card(CardPosition(5, 2), 2, 3)  # 5H
        game_state.create_gap(2, 4)  # Gap after 5H (should be playable by 6H)
        
        game_state.create_gap(3, 0)  # Gap in column 1 (should be playable by 2s)
        
        # Place some 2s and 6H to make moves possible
        game_state.place_card(CardPosition(2, 3), 2, 8)  # 2S not in column 1
        game_state.place_card(CardPosition(6, 2), 1, 10)  # 6H
        
        legal_moves = game_state.get_legal_moves()
        legitimate_gaps = self._count_legitimate_gaps(game_state)
        
        print(f"Legitimate gaps: {legitimate_gaps}")
        print(f"Legal moves: {len(legal_moves)}")
        
        assert legitimate_gaps < 4, "Should have less than 4 legitimate gaps"
        assert len(legal_moves) > 0, "Should have legal moves when less than 4 legitimate gaps"
        
        # Scenario 2: Exactly 4 legitimate gaps - should have no legal moves
        print("\n=== Scenario 2: 4 legitimate gaps ===")
        
        game_state2 = GameState(enable_diagnostics=False)
        
        # Create 4 gaps after Kings
        game_state2.place_card(CardPosition(13, 0), 0, 5)  # King
        game_state2.create_gap(0, 6)  # Gap after King
        
        game_state2.place_card(CardPosition(13, 1), 1, 7)  # King
        game_state2.create_gap(1, 8)  # Gap after King
        
        game_state2.place_card(CardPosition(13, 2), 2, 9)  # King
        game_state2.create_gap(2, 10)  # Gap after King
        
        game_state2.place_card(CardPosition(13, 3), 3, 11)  # King
        game_state2.create_gap(3, 12)  # Gap after King
        
        legal_moves2 = game_state2.get_legal_moves()
        legitimate_gaps2 = self._count_legitimate_gaps(game_state2)
        
        print(f"Legitimate gaps: {legitimate_gaps2}")
        print(f"Legal moves: {len(legal_moves2)}")
        
        assert legitimate_gaps2 == 4, "Should have exactly 4 legitimate gaps"
        assert len(legal_moves2) == 0, "Should have no legal moves when all 4 gaps are legitimate"
        
        # Scenario 3: 4 gaps but some are playable - should have legal moves  
        print("\n=== Scenario 3: 4 gaps, some playable ===")
        
        game_state3 = GameState(enable_diagnostics=False)
        
        # Create 2 gaps after Kings (legitimate)
        game_state3.place_card(CardPosition(13, 0), 0, 5)
        game_state3.create_gap(0, 6)
        
        game_state3.place_card(CardPosition(13, 1), 1, 7)
        game_state3.create_gap(1, 8)
        
        # Create 2 playable gaps
        game_state3.create_gap(2, 0)  # Column 1 gap
        game_state3.place_card(CardPosition(4, 2), 3, 3)  # 4H
        game_state3.create_gap(3, 4)  # Gap after 4H (playable by 5H)
        
        # Add cards that can fill the playable gaps
        game_state3.place_card(CardPosition(2, 3), 2, 8)  # 2S
        game_state3.place_card(CardPosition(5, 2), 1, 10)  # 5H
        
        legal_moves3 = game_state3.get_legal_moves()
        legitimate_gaps3 = self._count_legitimate_gaps(game_state3)
        
        print(f"Legitimate gaps: {legitimate_gaps3}")
        print(f"Legal moves: {len(legal_moves3)}")
        
        assert legitimate_gaps3 < 4, "Should have less than 4 legitimate gaps"
        assert len(legal_moves3) > 0, "Should have legal moves when some gaps are playable"
        
        print("✓ test_move_generation_stops_only_at_4_legitimate_gaps passed")
    
    def test_gap_after_gap_creates_legitimate_gaps(self):
        """Test that gaps after other gaps are counted as legitimate (unplayable)."""
        game_state = GameState(enable_diagnostics=False)
        
        # Create a chain: [card, gap, gap, gap, gap]
        game_state.place_card(CardPosition(5, 0), 0, 0)  # 5C
        game_state.create_gap(0, 1)  # Gap after card (playable)
        game_state.create_gap(0, 2)  # Gap after gap (legitimate)
        game_state.create_gap(0, 3)  # Gap after gap (legitimate)
        game_state.create_gap(0, 4)  # Gap after gap (legitimate)
        
        legitimate_gaps = self._count_legitimate_gaps(game_state)
        legal_moves = game_state.get_legal_moves()
        
        print(f"Gaps after gaps count as legitimate: {legitimate_gaps}")
        print(f"Legal moves available: {len(legal_moves)}")
        
        # Should have 3 legitimate gaps (positions 2, 3, 4) and 1 playable gap (position 1)
        assert legitimate_gaps == 3, f"Expected 3 legitimate gaps, got {legitimate_gaps}"
        
        # Should have legal moves because only the first gap is playable
        # (assuming we have a 6C somewhere to play after the 5C)
        
        print("✓ test_gap_after_gap_creates_legitimate_gaps passed")
    
    def _count_legitimate_gaps(self, game_state: GameState) -> int:
        """Count gaps that are legitimately unplayable (after Kings or after other gaps)."""
        legitimate_count = 0
        
        for gap_row, gap_col in game_state.gaps:
            if gap_col == 0:
                # First column gaps are always playable (by 2s not in column 1)
                continue
            
            # Check what's to the left of this gap
            prev_card = game_state.board[gap_row][gap_col - 1]
            
            if prev_card is None:
                # Gap after gap - legitimate (unplayable)
                legitimate_count += 1
            elif prev_card.rank == 13:
                # Gap after King - legitimate (unplayable)
                legitimate_count += 1
            # Otherwise it's a playable gap
        
        return legitimate_count


if __name__ == "__main__":
    test = TestMoveSimulationLimits()
    test.test_move_generation_stops_only_at_4_legitimate_gaps()
    test.test_gap_after_gap_creates_legitimate_gaps()
    print("\nAll move simulation limit tests passed!")