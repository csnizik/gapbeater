#!/usr/bin/env python3
"""
Verification script to ensure optimized evaluator produces identical results to original.

This script tests that the optimized PositionEvaluator produces exactly the same
scores as the original implementation on a variety of game states.
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from src.simulator.game_state import GameState, CardPosition
from src.simulator.evaluator import PositionEvaluator


def create_test_game_states():
    """Create comprehensive set of test game states."""
    states = []
    
    # 1. Empty board
    empty_state = GameState(enable_diagnostics=False)
    states.append(("Empty board", empty_state))
    
    # 2. Single correct placement
    single_placement = GameState(enable_diagnostics=False)
    single_placement.place_card(CardPosition(2, 0), 0, 0)
    single_placement.detect_immutable_sequences()
    states.append(("Single correct placement", single_placement))
    
    # 3. Multiple correct placements
    multi_placement = GameState(enable_diagnostics=False)
    for i in range(3):
        multi_placement.place_card(CardPosition(2 + i, 0), 0, i)
    multi_placement.detect_immutable_sequences()
    states.append(("Multiple correct placements", multi_placement))
    
    # 4. Dead gap only
    dead_gap_only = GameState(enable_diagnostics=False)
    dead_gap_only.place_card(CardPosition(13, 0), 0, 5)
    dead_gap_only.create_gap(0, 6)
    states.append(("Dead gap only", dead_gap_only))
    
    # 5. Multiple dead gaps
    multi_dead_gaps = GameState(enable_diagnostics=False)
    for i in range(3):
        multi_dead_gaps.place_card(CardPosition(13, i), i, 7)
        multi_dead_gaps.create_gap(i, 8)
    states.append(("Multiple dead gaps", multi_dead_gaps))
    
    # 6. Mixed: correct placements and dead gaps
    mixed_state = GameState(enable_diagnostics=False)
    # Correct placements
    for i in range(2):
        mixed_state.place_card(CardPosition(2 + i, 0), 0, i)
    # Dead gaps
    mixed_state.place_card(CardPosition(13, 1), 1, 8)
    mixed_state.create_gap(1, 9)
    mixed_state.detect_immutable_sequences()
    states.append(("Mixed correct placements and dead gaps", mixed_state))
    
    # 7. Complex realistic state
    complex_state = GameState(enable_diagnostics=False)
    placements = [
        (CardPosition(2, 0), 0, 0),
        (CardPosition(3, 0), 0, 1),
        (CardPosition(4, 0), 0, 2),
        (CardPosition(5, 0), 0, 3),
        (CardPosition(2, 1), 1, 0),
        (CardPosition(3, 1), 1, 1),
        (CardPosition(13, 2), 2, 10),
        (CardPosition(13, 3), 3, 8),
    ]
    for card, row, col in placements:
        complex_state.place_card(card, row, col)
    
    complex_state.create_gap(2, 11)  # Dead gap after King
    complex_state.create_gap(3, 9)   # Dead gap after King
    complex_state.create_gap(1, 5)   # Regular gap
    complex_state.detect_immutable_sequences()
    states.append(("Complex realistic state", complex_state))
    
    # 8. Nearly full board
    full_state = GameState(enable_diagnostics=False)
    for row in range(4):
        for col in range(12):  # Fill most positions
            rank = (col % 10) + 2  # Ranks 2-11, cycling
            card = CardPosition(rank, row)
            full_state.place_card(card, row, col)
    full_state.detect_immutable_sequences()
    states.append(("Nearly full board", full_state))
    
    return states


def verify_identical_results():
    """Verify that optimized and original evaluation methods produce identical results."""
    print("Verifying optimized evaluator produces identical results...")
    print("=" * 60)
    
    test_states = create_test_game_states()
    
    # Create evaluators with both configurations
    original_evaluator = PositionEvaluator(enable_performance_tracking=True)
    optimized_evaluator = PositionEvaluator(enable_performance_tracking=False)
    
    all_passed = True
    
    for state_name, state in test_states:
        # Get scores from both evaluators
        original_score = original_evaluator.evaluate(state)
        optimized_score = optimized_evaluator.evaluate(state)
        
        # Check if scores are identical (within floating point precision)
        score_match = abs(original_score - optimized_score) < 1e-10
        
        print(f"Testing: {state_name}")
        print(f"  Original score:  {original_score:.10f}")
        print(f"  Optimized score: {optimized_score:.10f}")
        print(f"  Match: {'✅' if score_match else '❌'}")
        
        if not score_match:
            print(f"  ERROR: Score mismatch! Difference: {abs(original_score - optimized_score)}")
            all_passed = False
        
        print()
    
    return all_passed


def verify_dead_gap_optimization():
    """Verify that the optimized dead gap counting produces identical results."""
    print("\nVerifying optimized dead gap counting...")
    print("=" * 40)
    
    # Create evaluator instance to access both methods
    evaluator = PositionEvaluator()
    
    test_states = create_test_game_states()
    all_passed = True
    
    for state_name, state in test_states:
        # Test both dead gap counting methods
        original_count = evaluator._count_dead_gaps(state)
        optimized_count = evaluator._count_dead_gaps_optimized(state)
        
        count_match = original_count == optimized_count
        
        print(f"Testing: {state_name}")
        print(f"  Original count:  {original_count}")
        print(f"  Optimized count: {optimized_count}")
        print(f"  Match: {'✅' if count_match else '❌'}")
        
        if not count_match:
            print(f"  ERROR: Dead gap count mismatch!")
            all_passed = False
        
        print()
    
    return all_passed


def main():
    """Main verification execution."""
    print("PositionEvaluator Optimization Verification")
    print("=" * 50)
    
    try:
        # Verify overall results are identical
        results_match = verify_identical_results()
        
        # Verify dead gap counting optimization
        dead_gap_match = verify_dead_gap_optimization()
        
        overall_success = results_match and dead_gap_match
        
        print("=" * 60)
        print("VERIFICATION SUMMARY")
        print("=" * 60)
        print(f"Score results match: {'✅ PASS' if results_match else '❌ FAIL'}")
        print(f"Dead gap counting match: {'✅ PASS' if dead_gap_match else '❌ FAIL'}")
        print(f"Overall verification: {'✅ PASS' if overall_success else '❌ FAIL'}")
        
        if overall_success:
            print("\n🎉 All optimizations verified - identical results maintained!")
            sys.exit(0)
        else:
            print("\n💥 Verification failed - optimizations changed results!")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 Verification error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()