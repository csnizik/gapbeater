#!/usr/bin/env python3
"""
CI integration script for PositionEvaluator performance regression testing.

This script is designed to be run in CI to ensure the evaluator maintains
the required performance threshold of 50,000 evaluations per second.
"""

import sys
import os
import time

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from src.simulator.game_state import GameState, CardPosition
from src.simulator.evaluator import PositionEvaluator


def run_ci_performance_test() -> bool:
    """
    Run a performance test suitable for CI environment.
    
    Uses a smaller number of evaluations to complete quickly while
    still providing accurate performance measurements.
    
    Returns:
        bool: True if performance meets target, False otherwise
    """
    print("Running CI Performance Test for PositionEvaluator...")
    
    # Create a representative game state
    state = GameState(enable_diagnostics=False)
    
    # Add some complexity to make it representative
    cards_to_place = [
        (CardPosition(2, 0), 0, 0),
        (CardPosition(3, 0), 0, 1),
        (CardPosition(4, 0), 0, 2),
        (CardPosition(13, 1), 1, 8),
        (CardPosition(13, 2), 2, 10),
    ]
    
    for card, row, col in cards_to_place:
        state.place_card(card, row, col)
    
    # Create some gaps including dead ones
    state.create_gap(1, 9)  # Dead gap after King
    state.create_gap(2, 11)  # Dead gap after King
    state.create_gap(3, 5)   # Regular gap
    
    state.detect_immutable_sequences()
    
    # Create evaluator with performance tracking disabled for max speed
    evaluator = PositionEvaluator(enable_performance_tracking=False)
    
    # Warmup
    for _ in range(100):
        evaluator.evaluate(state)
    
    # Run performance test
    num_evaluations = 25000  # Smaller number for CI
    start_time = time.perf_counter()
    
    for _ in range(num_evaluations):
        score = evaluator.evaluate(state)
    
    end_time = time.perf_counter()
    
    # Calculate performance metrics
    total_time = end_time - start_time
    avg_time_per_eval = total_time / num_evaluations
    evaluations_per_second = num_evaluations / total_time
    
    # Performance requirements
    target_eval_per_sec = 50000
    target_max_time_per_eval = 0.00002  # 20 microseconds
    
    # Check if targets are met
    speed_target_met = evaluations_per_second >= target_eval_per_sec
    time_target_met = avg_time_per_eval <= target_max_time_per_eval
    
    # Report results
    print(f"Evaluations performed: {num_evaluations:,}")
    print(f"Total time: {total_time:.4f} seconds")
    print(f"Average time per evaluation: {avg_time_per_eval:.8f} seconds")
    print(f"Evaluations per second: {evaluations_per_second:,.0f}")
    print(f"")
    print(f"Target: >= {target_eval_per_sec:,} eval/s")
    print(f"Target: <= {target_max_time_per_eval:.8f} s per eval")
    print(f"")
    
    if speed_target_met and time_target_met:
        print("✅ PERFORMANCE TEST PASSED")
        speedup = evaluations_per_second / target_eval_per_sec
        print(f"🚀 Performance is {speedup:.1f}x faster than minimum requirement")
        return True
    else:
        print("❌ PERFORMANCE TEST FAILED")
        if not speed_target_met:
            shortfall = target_eval_per_sec - evaluations_per_second
            print(f"   Speed shortfall: {shortfall:,.0f} eval/s")
        if not time_target_met:
            excess = avg_time_per_eval - target_max_time_per_eval
            print(f"   Time excess: {excess:.8f} s per eval")
        return False


def main():
    """Main CI test execution."""
    print("PositionEvaluator CI Performance Regression Test")
    print("=" * 50)
    
    try:
        success = run_ci_performance_test()
        
        if success:
            print("\n🎉 CI Performance test PASSED - No performance regression detected")
            sys.exit(0)
        else:
            print("\n💥 CI Performance test FAILED - Performance regression detected")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 CI Performance test ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()