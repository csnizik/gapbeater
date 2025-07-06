#!/usr/bin/env python3
"""
Micro-benchmark harness for PositionEvaluator performance testing.

This script measures evaluation throughput on representative GameState instances
to ensure the evaluator meets the target of 50,000+ evaluations per second.
"""

import sys
import os
import time
import cProfile
import pstats
from typing import List

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from src.simulator.game_state import GameState, CardPosition
from src.simulator.evaluator import PositionEvaluator


def create_representative_game_states() -> List[GameState]:
    """Create a variety of representative game states for benchmarking."""
    states = []
    
    # 1. Empty board
    empty_state = GameState(enable_diagnostics=False)
    states.append(empty_state)
    
    # 2. Board with some correct placements
    placement_state = GameState(enable_diagnostics=False)
    cards_to_place = [
        (CardPosition(2, 0), 0, 0),  # 2 of Clubs in correct position
        (CardPosition(3, 0), 0, 1),  # 3 of Clubs in correct position
        (CardPosition(4, 0), 0, 2),  # 4 of Clubs in correct position
        (CardPosition(2, 1), 1, 0),  # 2 of Diamonds in correct position
        (CardPosition(2, 2), 2, 0),  # 2 of Hearts in correct position
    ]
    for card, row, col in cards_to_place:
        placement_state.place_card(card, row, col)
    placement_state.detect_immutable_sequences()
    states.append(placement_state)
    
    # 3. Board with dead gaps
    dead_gap_state = GameState(enable_diagnostics=False)
    # Place Kings and create gaps after them
    for suit in range(4):
        king = CardPosition(13, suit)
        dead_gap_state.place_card(king, suit, 8)
        dead_gap_state.create_gap(suit, 9)
    states.append(dead_gap_state)
    
    # 4. Complex mixed state
    complex_state = GameState(enable_diagnostics=False)
    # Mix of correct placements, misplaced cards, and gaps
    mixed_placements = [
        (CardPosition(2, 0), 0, 0),
        (CardPosition(3, 0), 0, 1),
        (CardPosition(4, 0), 0, 2),
        (CardPosition(7, 1), 1, 5),  # Misplaced card
        (CardPosition(13, 2), 2, 10),  # King not at end
        (CardPosition(5, 3), 3, 3),   # Partially correct sequence
        (CardPosition(6, 3), 3, 4),
    ]
    for card, row, col in mixed_placements:
        complex_state.place_card(card, row, col)
    
    # Add some gaps
    complex_state.create_gap(0, 3)
    complex_state.create_gap(1, 7)
    complex_state.create_gap(2, 11)  # Dead gap after King
    
    complex_state.detect_immutable_sequences()
    states.append(complex_state)
    
    # 5. Nearly complete board
    complete_state = GameState(enable_diagnostics=False)
    # Fill most positions with correct sequences
    for row in range(4):
        for col in range(10):  # Fill first 10 columns
            rank = col + 2  # Ranks 2-11
            card = CardPosition(rank, row)
            complete_state.place_card(card, row, col)
    complete_state.detect_immutable_sequences()
    states.append(complete_state)
    
    return states


def run_benchmark(num_evaluations: int = 100000, profile: bool = False) -> dict:
    """
    Run benchmark with specified number of evaluations.
    
    Args:
        num_evaluations: Number of evaluations to perform
        profile: Whether to run with cProfile enabled
        
    Returns:
        dict: Benchmark results including timing and throughput
    """
    print(f"Running benchmark with {num_evaluations:,} evaluations...")
    
    # Create test states
    test_states = create_representative_game_states()
    print(f"Created {len(test_states)} representative game states")
    
    # Create evaluator
    evaluator = PositionEvaluator()
    
    # Warmup
    for state in test_states:
        evaluator.evaluate(state)
    
    if profile:
        # Run with profiling
        profiler = cProfile.Profile()
        profiler.enable()
    
    # Run benchmark
    start_time = time.perf_counter()
    
    state_idx = 0
    for i in range(num_evaluations):
        # Cycle through different states for variety
        state = test_states[state_idx]
        score = evaluator.evaluate(state)
        state_idx = (state_idx + 1) % len(test_states)
    
    end_time = time.perf_counter()
    
    if profile:
        profiler.disable()
        
        # Save profiling results
        stats = pstats.Stats(profiler)
        stats.sort_stats('cumulative')
        stats.print_stats(20)  # Print top 20 functions
        
        # Save to file for detailed analysis
        stats.dump_stats('evaluator_profile.prof')
        print("\nProfile saved to evaluator_profile.prof")
    
    # Calculate results
    total_time = end_time - start_time
    avg_time_per_eval = total_time / num_evaluations
    evaluations_per_second = num_evaluations / total_time
    
    # Get evaluator's internal performance stats
    internal_stats = evaluator.get_performance_stats()
    
    results = {
        'num_evaluations': num_evaluations,
        'total_time': total_time,
        'avg_time_per_eval': avg_time_per_eval,
        'evaluations_per_second': evaluations_per_second,
        'target_met': evaluations_per_second >= 50000,
        'target_threshold': 50000,
        'internal_stats': internal_stats
    }
    
    return results


def print_results(results: dict):
    """Print benchmark results in a formatted way."""
    print("\n" + "="*60)
    print("POSITION EVALUATOR BENCHMARK RESULTS")
    print("="*60)
    
    print(f"Evaluations performed: {results['num_evaluations']:,}")
    print(f"Total time: {results['total_time']:.4f} seconds")
    print(f"Average time per evaluation: {results['avg_time_per_eval']:.8f} seconds")
    print(f"Evaluations per second: {results['evaluations_per_second']:,.0f}")
    print(f"Target threshold: {results['target_threshold']:,} eval/s")
    
    if results['target_met']:
        print("✅ TARGET MET: Performance exceeds 50,000 evaluations/second")
    else:
        shortfall = results['target_threshold'] - results['evaluations_per_second']
        print(f"❌ TARGET MISSED: Need {shortfall:,.0f} more eval/s to meet target")
    
    print("\nInternal evaluator stats:")
    internal = results['internal_stats']
    print(f"  Evaluation count: {internal['evaluation_count']:,}")
    print(f"  Total time: {internal['total_time']:.4f}s")
    print(f"  Average time: {internal['average_time']:.8f}s")
    print(f"  Eval/sec: {internal['evaluations_per_second']:,.0f}")


def main():
    """Main benchmark execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Benchmark PositionEvaluator performance')
    parser.add_argument('--evaluations', '-n', type=int, default=100000,
                      help='Number of evaluations to perform (default: 100,000)')
    parser.add_argument('--profile', '-p', action='store_true',
                      help='Enable profiling to identify hotspots')
    parser.add_argument('--quick', '-q', action='store_true',
                      help='Quick test with 10,000 evaluations')
    
    args = parser.parse_args()
    
    if args.quick:
        num_evaluations = 10000
    else:
        num_evaluations = args.evaluations
    
    try:
        results = run_benchmark(num_evaluations, profile=args.profile)
        print_results(results)
        
        # Exit with error code if target not met
        if not results['target_met']:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\nBenchmark interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nBenchmark failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()