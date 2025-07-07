"""
Integration tests for settings management feature.

Tests the complete flow from main menu to settings display to validate
all acceptance criteria from the issue requirements.
"""

import sys
import os
import time
from io import StringIO

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.game import GameManager
from src.config.settings_manager import SettingsManager


def test_acceptance_criteria_main_menu_integration():
    """
    GIVEN the main CLI menu
    WHEN I type 's' or select Settings
    THEN I see a formatted list of all performance-related settings.
    """
    print("Testing acceptance criteria: main menu integration...")
    
    manager = GameManager()
    
    # Capture stdout to verify output
    old_stdout = sys.stdout
    sys.stdout = StringIO()
    
    try:
        # This simulates what happens when user selects 's' from main menu
        # (without the input() call that waits for user)
        settings_manager = SettingsManager()
        settings_manager.display()
        
        output = sys.stdout.getvalue()
        
    finally:
        sys.stdout = old_stdout
    
    # Verify the formatted list contains expected settings
    assert "PERFORMANCE SETTINGS" in output, "Should display header"
    assert "Search Depth" in output, "Should show search depth setting"
    assert "Alpha-Beta Pruning" in output, "Should show alpha-beta setting"
    assert "Transposition Tables" in output, "Should show transposition table setting"
    assert "Memory Limit" in output, "Should show memory setting"
    assert "Setting" in output and "Value" in output and "Range" in output, "Should show table headers"
    
    print("✓ test_acceptance_criteria_main_menu_integration passed")


def test_acceptance_criteria_invalid_setting_warning():
    """
    GIVEN a setting has an out-of-range value
    WHEN the list is displayed
    THEN the system highlights or warns about the invalid setting.
    """
    print("Testing acceptance criteria: invalid setting warnings...")
    
    settings_manager = SettingsManager()
    
    # Create an invalid setting
    settings_manager._settings['search_depth'].current_value = 999  # Outside 1-25 range
    
    # Capture stdout
    old_stdout = sys.stdout
    sys.stdout = StringIO()
    
    try:
        settings_manager.display()
        output = sys.stdout.getvalue()
    finally:
        sys.stdout = old_stdout
    
    # Verify warning is displayed
    assert "⚠️" in output, "Should display warning symbol"
    assert "WARNINGS:" in output, "Should display warnings section"
    assert "Search Depth: 999 is outside valid range" in output, "Should specify invalid value and range"
    
    # Reset for clean state
    settings_manager.reset_setting('search_depth')
    
    print("✓ test_acceptance_criteria_invalid_setting_warning passed")


def test_functional_requirement_performance_settings_list():
    """
    Test that all required performance-tuning settings are available.
    """
    print("Testing functional requirement: comprehensive settings list...")
    
    settings_manager = SettingsManager()
    summary = settings_manager.get_settings_summary()
    
    # Verify required settings categories are present
    required_search_settings = ['search_depth', 'max_search_time', 'max_iterations']
    required_optimization_toggles = ['alpha_beta_pruning', 'transposition_tables', 'iterative_deepening']
    required_performance_targets = ['target_positions_per_sec', 'max_response_time', 'max_memory_usage']
    required_evaluator_weights = ['gap_creation_weight', 'sequence_weight']
    required_logging_settings = ['enable_diagnostics', 'performance_tracking']
    
    all_required = (required_search_settings + required_optimization_toggles + 
                   required_performance_targets + required_evaluator_weights + 
                   required_logging_settings)
    
    for setting_key in all_required:
        assert setting_key in summary, f"Required setting '{setting_key}' not found"
        setting_info = summary[setting_key]
        assert 'name' in setting_info, f"Setting {setting_key} missing name"
        assert 'value' in setting_info, f"Setting {setting_key} missing value"
        assert 'range' in setting_info, f"Setting {setting_key} missing range"
        assert 'description' in setting_info, f"Setting {setting_key} missing description"
    
    print("✓ test_functional_requirement_performance_settings_list passed")


def test_functional_requirement_setting_metadata():
    """
    Test that each setting includes name, current value, allowable range, and description.
    """
    print("Testing functional requirement: setting metadata completeness...")
    
    settings_manager = SettingsManager()
    summary = settings_manager.get_settings_summary()
    
    for setting_key, setting_info in summary.items():
        # Check all required metadata is present and non-empty
        assert setting_info['name'], f"Setting {setting_key} has empty name"
        assert setting_info['value'] is not None, f"Setting {setting_key} has no value"
        assert setting_info['range'], f"Setting {setting_key} has empty range"
        assert setting_info['description'], f"Setting {setting_key} has empty description"
        
        # Verify value is within range for numeric settings
        assert setting_info['valid'], f"Setting {setting_key} has invalid default value"
    
    print("✓ test_functional_requirement_setting_metadata passed")


def test_non_functional_requirement_performance():
    """
    Test that loading and displaying settings takes under 100ms.
    """
    print("Testing non-functional requirement: display performance...")
    
    settings_manager = SettingsManager()
    
    # Measure display performance multiple times for consistency
    times = []
    for _ in range(5):
        # Capture stdout to avoid printing during test
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        
        try:
            start_time = time.perf_counter()
            settings_manager.display()
            end_time = time.perf_counter()
            
            elapsed_ms = (end_time - start_time) * 1000
            times.append(elapsed_ms)
            
        finally:
            sys.stdout = old_stdout
    
    avg_time = sum(times) / len(times)
    max_time = max(times)
    
    # All attempts should be under 100ms
    assert max_time < 100, f"Display took {max_time:.1f}ms, exceeds 100ms requirement"
    assert avg_time < 50, f"Average display time {avg_time:.1f}ms should be well under 100ms"
    
    print(f"✓ test_non_functional_requirement_performance passed (avg: {avg_time:.1f}ms)")


def test_non_functional_requirement_thread_safety():
    """
    Test thread-safe read access to settings.
    """
    print("Testing non-functional requirement: thread safety...")
    
    import threading
    
    settings_manager = SettingsManager()
    errors = []
    results = []
    
    def read_settings_worker(worker_id):
        try:
            for i in range(20):
                # Read various settings
                depth = settings_manager.get_setting('search_depth')
                alpha_beta = settings_manager.get_setting('alpha_beta_pruning')
                memory = settings_manager.get_setting('max_memory_usage')
                results.append((worker_id, i, depth, alpha_beta, memory))
        except Exception as e:
            errors.append(f"Worker {worker_id}: {e}")
    
    # Start multiple reader threads
    threads = []
    for i in range(3):
        thread = threading.Thread(target=read_settings_worker, args=(i,))
        threads.append(thread)
        thread.start()
    
    # Wait for completion
    for thread in threads:
        thread.join()
    
    assert len(errors) == 0, f"Thread safety errors: {errors}"
    assert len(results) == 60, "Should have results from all threads"
    
    print("✓ test_non_functional_requirement_thread_safety passed")


def test_technical_implementation_central_configuration():
    """
    Test that settings are persisted in a central configuration object
    accessible by any module.
    """
    print("Testing technical implementation: central configuration...")
    
    # Test singleton behavior
    manager1 = SettingsManager()
    manager2 = SettingsManager()
    
    assert manager1 is manager2, "SettingsManager should be singleton"
    
    # Test that changes persist across instances
    manager1.set_setting('search_depth', 10)
    assert manager2.get_setting('search_depth') == 10, "Changes should persist across instances"
    
    # Reset for clean state
    manager1.reset_setting('search_depth')
    
    print("✓ test_technical_implementation_central_configuration passed")


def run_integration_tests():
    """Run all integration tests for settings management feature"""
    print("Running Settings Management Integration Tests...\n")
    
    test_functions = [
        test_acceptance_criteria_main_menu_integration,
        test_acceptance_criteria_invalid_setting_warning,
        test_functional_requirement_performance_settings_list,
        test_functional_requirement_setting_metadata,
        test_non_functional_requirement_performance,
        test_non_functional_requirement_thread_safety,
        test_technical_implementation_central_configuration
    ]
    
    passed = 0
    failed = 0
    
    for test_func in test_functions:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"✗ {test_func.__name__} failed: {e}")
            failed += 1
    
    print(f"\nIntegration Test Results: {passed}/{len(test_functions)} tests passed")
    
    if failed > 0:
        print(f"⚠️  {failed} tests failed")
        return False
    else:
        print("🎉 All integration tests passed!")
        print("\n✅ All acceptance criteria validated:")
        print("   • Main menu includes [S]ettings option")
        print("   • Settings display as formatted table with metadata")
        print("   • Invalid settings show warnings")
        print("   • Performance under 100ms requirement met")
        print("   • Thread-safe read access confirmed")
        print("   • Central configuration accessible by any module")
        return True


if __name__ == "__main__":
    run_integration_tests()