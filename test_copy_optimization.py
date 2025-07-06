#!/usr/bin/env python3
"""
Performance test specifically for GameState.copy() to validate optimization requirements.

This test validates that:
1. Average copy time < 0.0001s per call (acceptance criteria)
2. Copy preserves deep-copy semantics 
3. Diagnostics and caches remain consistent
"""

import sys
import os
import time
from typing import List

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from src.simulator.game_state import GameState, CardPosition


def test_copy_performance():
    """Test that copy method meets performance requirements."""
    print("="*60)
    print("GAMESTATE COPY PERFORMANCE VALIDATION")
    print("="*60)
    
    # Create representative game states
    states = []
    
    # Empty board
    empty = GameState(enable_diagnostics=False)
    states.append(("empty", empty))
    
    # Partially filled board
    partial = GameState(enable_diagnostics=False)
    cards = [
        (CardPosition(2, 0), 0, 0), (CardPosition(3, 0), 0, 1),
        (CardPosition(2, 1), 1, 0), (CardPosition(3, 1), 1, 1),
        (CardPosition(2, 2), 2, 0), (CardPosition(2, 3), 3, 0),
    ]
    for card, row, col in cards:
        partial.place_card(card, row, col)
    partial.detect_immutable_sequences()
    states.append(("partial", partial))
    
    # Nearly full board
    full = GameState(enable_diagnostics=False)
    for row in range(4):
        for col in range(10):
            rank = col + 2
            card = CardPosition(rank, row)
            full.place_card(card, row, col)
    full.detect_immutable_sequences()
    states.append(("full", full))
    
    # Test performance requirement: 1000 copies, average < 0.0001s
    print("\n1. Performance Test (1000 copies)")
    print("-" * 40)
    
    num_copies = 1000
    total_time = 0.0
    copy_times = []
    
    for state_name, state in states:
        # Warmup
        for _ in range(50):
            state.copy()
            
        # Actual test
        state_times = []
        for _ in range(num_copies // len(states)):
            start = time.perf_counter()
            copied = state.copy()
            end = time.perf_counter()
            
            copy_time = end - start
            state_times.append(copy_time)
            copy_times.append(copy_time)
        
        avg_state_time = sum(state_times) / len(state_times)
        print(f"   {state_name:<8}: {avg_state_time:.8f}s avg")
    
    avg_copy_time = sum(copy_times) / len(copy_times)
    min_time = min(copy_times)
    max_time = max(copy_times)
    
    print(f"\nOVERALL RESULTS:")
    print(f"   Copies performed: {len(copy_times)}")
    print(f"   Average time: {avg_copy_time:.8f}s")
    print(f"   Min time: {min_time:.8f}s")
    print(f"   Max time: {max_time:.8f}s")
    print(f"   Target: < 0.0001s")
    
    performance_pass = avg_copy_time < 0.0001
    status = "✅ PASS" if performance_pass else "❌ FAIL"
    print(f"   Status: {status}")
    
    return performance_pass


def test_copy_correctness():
    """Test that copy preserves deep-copy semantics."""
    print("\n2. Deep-Copy Semantics Test")
    print("-" * 40)
    
    # Create original state
    original = GameState(enable_diagnostics=False)
    cards = [
        (CardPosition(2, 0), 0, 0),
        (CardPosition(3, 0), 0, 1),
        (CardPosition(2, 1), 1, 0),
    ]
    
    for card, row, col in cards:
        original.place_card(card, row, col)
    original.detect_immutable_sequences()
    
    # Create copy
    copied = original.copy()
    
    tests_passed = 0
    total_tests = 4
    
    # Test 1: Basic equality
    try:
        assert copied.board == original.board, "Board not equal"
        assert copied.gaps == original.gaps, "Gaps not equal" 
        assert copied.zhash == original.zhash, "Zhash not equal"
        print("   ✅ Basic equality test")
        tests_passed += 1
    except AssertionError as e:
        print(f"   ❌ Basic equality test: {e}")
    
    # Test 2: Independence - modify copy shouldn't affect original
    try:
        test_card = CardPosition(4, 0)
        copied.place_card(test_card, 0, 2)
        
        assert original.board[0][2] is None, "Original was modified"
        assert copied.board[0][2] == test_card, "Copy wasn't modified"
        print("   ✅ Independence test")
        tests_passed += 1
    except AssertionError as e:
        print(f"   ❌ Independence test: {e}")
    
    # Test 3: Row independence
    try:
        original_board_ref = original.board
        copied.board[1] = []  # Modify row in copy
        
        assert len(original.board[1]) > 0, "Original row was affected"
        print("   ✅ Row independence test")
        tests_passed += 1
    except AssertionError as e:
        print(f"   ❌ Row independence test: {e}")
    
    # Test 4: Immutable data sharing (should be safe)
    try:
        # Frozensets should be shared safely (immutable)
        assert copied.gaps is original.gaps or copied.gaps == original.gaps
        print("   ✅ Immutable data sharing test")
        tests_passed += 1
    except AssertionError as e:
        print(f"   ❌ Immutable data sharing test: {e}")
    
    correctness_pass = tests_passed == total_tests
    print(f"\n   Tests passed: {tests_passed}/{total_tests}")
    status = "✅ PASS" if correctness_pass else "❌ FAIL"
    print(f"   Status: {status}")
    
    return correctness_pass


def test_diagnostics_consistency():
    """Test that diagnostics and caches remain consistent."""
    print("\n3. Diagnostics & Cache Consistency Test")
    print("-" * 40)
    
    tests_passed = 0
    total_tests = 3
    
    # Test 1: Copy without diagnostics should not enable them
    try:
        state_no_diag = GameState(enable_diagnostics=False)
        copied = state_no_diag.copy()
        
        assert copied.diagnostics is None, "Diagnostics enabled in copy"
        print("   ✅ No diagnostics propagation test")
        tests_passed += 1
    except AssertionError as e:
        print(f"   ❌ No diagnostics propagation test: {e}")
    
    # Test 2: Copy with diagnostics should log performance
    try:
        state_with_diag = GameState(enable_diagnostics=True)
        state_with_diag.place_card(CardPosition(2, 0), 0, 0)
        
        initial_copy_count = len(state_with_diag.diagnostics.position_copy_times)
        copied = state_with_diag.copy()
        final_copy_count = len(state_with_diag.diagnostics.position_copy_times)
        
        assert final_copy_count > initial_copy_count, "Copy time not logged"
        assert copied.diagnostics is None, "Diagnostics enabled in copy"
        print("   ✅ Diagnostics logging test")
        tests_passed += 1
    except AssertionError as e:
        print(f"   ❌ Diagnostics logging test: {e}")
    
    # Test 3: Caches should be clean in copy
    try:
        state = GameState(enable_diagnostics=False)
        state.place_card(CardPosition(2, 0), 0, 0)
        
        # Populate cache
        moves = state.get_legal_moves()
        assert state._legal_moves_cache is not None, "Cache not populated"
        
        # Copy should have clean caches
        copied = state.copy()
        assert copied._legal_moves_cache is None, "Cache copied"
        assert copied._evaluation_cache is None, "Eval cache copied"
        print("   ✅ Clean caches test")
        tests_passed += 1
    except AssertionError as e:
        print(f"   ❌ Clean caches test: {e}")
    
    consistency_pass = tests_passed == total_tests
    print(f"\n   Tests passed: {tests_passed}/{total_tests}")
    status = "✅ PASS" if consistency_pass else "❌ FAIL"
    print(f"   Status: {status}")
    
    return consistency_pass


def main():
    """Run all copy optimization validation tests."""
    print("Running GameState copy optimization validation...")
    
    # Run all tests
    performance_pass = test_copy_performance()
    correctness_pass = test_copy_correctness()
    consistency_pass = test_diagnostics_consistency()
    
    # Final summary
    print("\n" + "="*60)
    print("FINAL VALIDATION SUMMARY")
    print("="*60)
    
    all_pass = performance_pass and correctness_pass and consistency_pass
    
    print(f"Performance (< 0.0001s): {'✅ PASS' if performance_pass else '❌ FAIL'}")
    print(f"Deep-copy semantics:     {'✅ PASS' if correctness_pass else '❌ FAIL'}")
    print(f"Diagnostics/caches:      {'✅ PASS' if consistency_pass else '❌ FAIL'}")
    print()
    print(f"OVERALL: {'✅ ALL REQUIREMENTS MET' if all_pass else '❌ REQUIREMENTS NOT MET'}")
    
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())