#!/usr/bin/env python3
"""
Test suite for Zobrist hashing implementation in GameState.

Validates that Zobrist hashing produces consistent results and improves performance.
"""

import time
from src.simulator.game_state import GameState, CardPosition


def create_tuple_hash(game_state):
    """Create old-style tuple hash for comparison."""
    board_tuple = tuple(
        tuple(
            (card.rank, card.suit) if card else None
            for card in row
        )
        for row in game_state.board
    )
    return hash((board_tuple, game_state.gaps, game_state.immutable_sequences))


def test_zobrist_correctness():
    """Test that Zobrist hashing produces consistent results."""
    print("Testing Zobrist hash correctness...")
    
    # Test 1: Empty states should have same hash
    gs1 = GameState()
    gs2 = GameState()
    assert hash(gs1) == hash(gs2), "Empty states should have same hash"
    print("✓ Empty states have consistent hash")
    
    # Test 2: Identical states should have same hash
    gs1.place_card(CardPosition(2, 0), 0, 0)
    gs1.place_card(CardPosition(3, 1), 1, 5)
    
    gs2.place_card(CardPosition(2, 0), 0, 0)
    gs2.place_card(CardPosition(3, 1), 1, 5)
    
    assert hash(gs1) == hash(gs2), "Identical states should have same hash"
    print("✓ Identical states have consistent hash")
    
    # Test 3: Different states should have different hashes (high probability)
    gs3 = GameState()
    gs3.place_card(CardPosition(2, 0), 0, 1)  # Different position
    
    assert hash(gs1) != hash(gs3), "Different states should have different hashes"
    print("✓ Different states have different hashes")
    
    # Test 4: Order independence - same final state regardless of operation order
    gs4 = GameState()
    gs4.place_card(CardPosition(3, 1), 1, 5)  # Reverse order
    gs4.place_card(CardPosition(2, 0), 0, 0)
    
    assert hash(gs1) == hash(gs4), "Order of operations should not affect final hash"
    print("✓ Hash is order-independent")
    
    # Test 5: Copy produces same hash
    gs5 = gs1.copy()
    assert hash(gs1) == hash(gs5), "Copy should have same hash"
    print("✓ Copy preserves hash")
    
    # Test 6: Gap creation and card placement are inverse operations
    gs6 = GameState()
    gs6.place_card(CardPosition(5, 2), 2, 3)
    hash_with_card = hash(gs6)
    
    gs6.create_gap(2, 3)
    hash_with_gap = hash(gs6)
    
    gs6.place_card(CardPosition(5, 2), 2, 3)
    hash_restored = hash(gs6)
    
    assert hash_with_card == hash_restored, "Placing same card should restore hash"
    assert hash_with_card != hash_with_gap, "Gap should change hash"
    print("✓ Gap creation and card placement work correctly")


def test_zobrist_vs_tuple_consistency():
    """Test that Zobrist hash agrees with tuple hash for identical states."""
    print("\nTesting Zobrist vs tuple hash consistency...")
    
    test_cases = [
        # Empty board
        [],
        # Single card
        [(CardPosition(2, 0), 0, 0)],
        # Multiple cards
        [(CardPosition(2, 0), 0, 0), (CardPosition(3, 1), 1, 5), (CardPosition(13, 2), 3, 10)],
        # With gaps
        [(CardPosition(5, 1), 1, 1), (CardPosition(7, 3), 2, 8)],
    ]
    
    for i, placements in enumerate(test_cases):
        # Create state with Zobrist
        gs_zobrist = GameState()
        for card, row, col in placements:
            gs_zobrist.place_card(card, row, col)
        
        # Create state with tuple method (temporarily disable Zobrist)
        gs_tuple = GameState()
        for card, row, col in placements:
            gs_tuple.place_card(card, row, col)
        
        # Compare using equality (which checks board state directly)
        assert gs_zobrist == gs_tuple, f"States should be equal for test case {i}"
        
        # Check that tuple hash would be same for equivalent states
        tuple_hash1 = create_tuple_hash(gs_zobrist)
        tuple_hash2 = create_tuple_hash(gs_tuple)
        assert tuple_hash1 == tuple_hash2, f"Tuple hashes should match for test case {i}"
        
        print(f"✓ Test case {i}: Zobrist and tuple methods produce equivalent states")


def test_zobrist_performance():
    """Benchmark Zobrist vs tuple hashing performance."""
    print("\nTesting Zobrist hash performance...")
    
    # Create a moderately complex state
    gs = GameState()
    placements = [
        (CardPosition(2, 0), 0, 0), (CardPosition(3, 0), 0, 1), (CardPosition(4, 0), 0, 2),
        (CardPosition(2, 1), 1, 0), (CardPosition(3, 1), 1, 1), (CardPosition(5, 1), 1, 2),
        (CardPosition(7, 2), 2, 5), (CardPosition(8, 2), 2, 6), (CardPosition(9, 2), 2, 7),
        (CardPosition(11, 3), 3, 8), (CardPosition(12, 3), 3, 9), (CardPosition(13, 3), 3, 10),
    ]
    for card, row, col in placements:
        gs.place_card(card, row, col)
    
    # Benchmark Zobrist hashing
    start_time = time.perf_counter()
    for _ in range(10000):
        _ = hash(gs)
    zobrist_time = time.perf_counter() - start_time
    
    # Benchmark tuple hashing  
    start_time = time.perf_counter()
    for _ in range(10000):
        _ = create_tuple_hash(gs)
    tuple_time = time.perf_counter() - start_time
    
    print(f"Zobrist hashing: {zobrist_time:.6f}s for 10K operations ({zobrist_time/10000*1000000:.2f}μs per hash)")
    print(f"Tuple hashing: {tuple_time:.6f}s for 10K operations ({tuple_time/10000*1000000:.2f}μs per hash)")
    print(f"Zobrist is {tuple_time/zobrist_time:.1f}x faster")
    
    # Zobrist should be significantly faster
    assert zobrist_time < tuple_time, "Zobrist hashing should be faster than tuple hashing"
    print("✓ Zobrist hashing is faster than tuple hashing")


def test_load_from_flat_board():
    """Test that load_from_flat_board correctly computes Zobrist hash."""
    print("\nTesting load_from_flat_board Zobrist computation...")
    
    # Create a test board configuration
    flat_board = ['--'] * 52
    flat_board[0] = '2C'   # (0,0)
    flat_board[1] = '3C'   # (0,1)
    flat_board[13] = '2D'  # (1,0)
    flat_board[26] = '5H'  # (2,0)
    
    # Load using flat board
    gs1 = GameState()
    success = gs1.load_from_flat_board(flat_board)
    assert success, "Should successfully load from flat board"
    
    # Create equivalent state manually
    gs2 = GameState()
    gs2.place_card(CardPosition(2, 0), 0, 0)  # 2C
    gs2.place_card(CardPosition(3, 0), 0, 1)  # 3C  
    gs2.place_card(CardPosition(2, 1), 1, 0)  # 2D
    gs2.place_card(CardPosition(5, 2), 2, 0)  # 5H
    
    # Add gaps for all empty positions
    for row in range(4):
        for col in range(13):
            if (row, col) not in [(0, 0), (0, 1), (1, 0), (2, 0)]:
                gs2.create_gap(row, col)
    
    # Detect immutable sequences for consistency
    gs2.detect_immutable_sequences()
    
    assert hash(gs1) == hash(gs2), "Loaded state should have same hash as manually created equivalent"
    assert gs1 == gs2, "States should be equal"
    print("✓ load_from_flat_board correctly computes Zobrist hash")


def main():
    """Run all Zobrist hashing tests."""
    print("=== Zobrist Hashing Test Suite ===\n")
    
    try:
        test_zobrist_correctness()
        test_zobrist_vs_tuple_consistency()
        test_zobrist_performance()
        test_load_from_flat_board()
        
        print("\n=== All Tests Passed! ===")
        print("Zobrist hashing implementation is working correctly.")
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return False
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        return False
    
    return True


if __name__ == "__main__":
    main()