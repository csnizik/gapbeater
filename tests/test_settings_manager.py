"""
Unit tests for SettingsManager.

Tests the central configuration management system for performance settings.
"""

import sys
import os
import time
import threading

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.config.settings_manager import SettingsManager, SettingType


def test_singleton_pattern():
    """Test that SettingsManager follows singleton pattern"""
    print("Testing singleton pattern...")
    
    manager1 = SettingsManager()
    manager2 = SettingsManager()
    
    assert manager1 is manager2, "SettingsManager should be a singleton"
    print("✓ test_singleton_pattern passed")


def test_default_settings_loaded():
    """Test that default settings are properly loaded"""
    print("Testing default settings loading...")
    
    manager = SettingsManager()
    
    # Test a few key settings exist
    expected_settings = [
        'search_depth', 'max_search_time', 'alpha_beta_pruning', 
        'transposition_tables', 'target_positions_per_sec'
    ]
    
    for setting_key in expected_settings:
        try:
            value = manager.get_setting(setting_key)
            assert value is not None, f"Setting {setting_key} should have a default value"
        except KeyError:
            assert False, f"Expected setting {setting_key} not found"
    
    print("✓ test_default_settings_loaded passed")


def test_get_set_setting():
    """Test getting and setting individual settings"""
    print("Testing get/set setting operations...")
    
    manager = SettingsManager()
    
    # Test getting existing setting
    original_depth = manager.get_setting('search_depth')
    assert isinstance(original_depth, int), "search_depth should be an integer"
    
    # Test setting valid value
    success = manager.set_setting('search_depth', 10)
    assert success, "Should be able to set valid value"
    assert manager.get_setting('search_depth') == 10, "Value should be updated"
    
    # Test setting invalid value (out of range)
    success = manager.set_setting('search_depth', 100)  # Should be outside max range
    assert not success, "Should reject out-of-range value"
    assert manager.get_setting('search_depth') == 10, "Value should remain unchanged"
    
    # Test setting invalid type
    success = manager.set_setting('search_depth', "invalid")
    assert not success, "Should reject wrong type"
    
    # Reset for clean test state
    manager.reset_setting('search_depth')
    
    print("✓ test_get_set_setting passed")


def test_boolean_settings():
    """Test boolean setting functionality"""
    print("Testing boolean settings...")
    
    manager = SettingsManager()
    
    # Test boolean setting
    original_value = manager.get_setting('alpha_beta_pruning')
    assert isinstance(original_value, bool), "alpha_beta_pruning should be boolean"
    
    # Toggle value
    new_value = not original_value
    success = manager.set_setting('alpha_beta_pruning', new_value)
    assert success, "Should be able to set boolean value"
    assert manager.get_setting('alpha_beta_pruning') == new_value, "Boolean value should be updated"
    
    # Reset
    manager.reset_setting('alpha_beta_pruning')
    
    print("✓ test_boolean_settings passed")


def test_float_settings():
    """Test float setting functionality"""
    print("Testing float settings...")
    
    manager = SettingsManager()
    
    # Test float setting
    original_value = manager.get_setting('max_search_time')
    
    # Set new float value
    success = manager.set_setting('max_search_time', 3.5)
    assert success, "Should be able to set float value"
    assert manager.get_setting('max_search_time') == 3.5, "Float value should be updated"
    
    # Test setting int for float (should convert)
    success = manager.set_setting('max_search_time', 5)
    assert success, "Should be able to set int for float"
    assert manager.get_setting('max_search_time') == 5.0, "Int should be converted to float"
    
    # Reset
    manager.reset_setting('max_search_time')
    
    print("✓ test_float_settings passed")


def test_invalid_setting_detection():
    """Test detection of invalid settings"""
    print("Testing invalid setting detection...")
    
    manager = SettingsManager()
    
    # Create an invalid setting by direct manipulation (simulating config file corruption)
    manager._settings['search_depth'].current_value = 999  # Outside valid range
    
    invalid_settings = manager.get_invalid_settings()
    assert 'search_depth' in invalid_settings, "Should detect invalid search_depth"
    
    # Reset to valid value
    manager.reset_setting('search_depth')
    
    invalid_settings = manager.get_invalid_settings()
    assert 'search_depth' not in invalid_settings, "Should not detect search_depth as invalid after reset"
    
    print("✓ test_invalid_setting_detection passed")


def test_reset_functionality():
    """Test reset functionality"""
    print("Testing reset functionality...")
    
    manager = SettingsManager()
    
    # Change some settings
    manager.set_setting('search_depth', 5)
    manager.set_setting('alpha_beta_pruning', False)
    
    # Reset single setting
    manager.reset_setting('search_depth')
    assert manager.get_setting('search_depth') == 15, "search_depth should be reset to default"
    assert manager.get_setting('alpha_beta_pruning') == False, "Other settings should remain changed"
    
    # Reset all settings
    manager.reset_all_settings()
    assert manager.get_setting('alpha_beta_pruning') == True, "All settings should be reset to defaults"
    
    print("✓ test_reset_functionality passed")


def test_display_performance():
    """Test that display() meets performance requirement (< 100ms)"""
    print("Testing display performance...")
    
    manager = SettingsManager()
    
    # Capture output by redirecting stdout temporarily
    import sys
    from io import StringIO
    
    old_stdout = sys.stdout
    sys.stdout = StringIO()
    
    try:
        start_time = time.perf_counter()
        manager.display()
        end_time = time.perf_counter()
        
        elapsed_ms = (end_time - start_time) * 1000
        assert elapsed_ms < 100, f"Display should take < 100ms, took {elapsed_ms:.1f}ms"
        
    finally:
        output = sys.stdout.getvalue()
        sys.stdout = old_stdout
    
    # Check that output contains expected content
    assert "PERFORMANCE SETTINGS" in output, "Output should contain header"
    assert "Search Depth" in output, "Output should contain search depth setting"
    assert "Alpha-Beta Pruning" in output, "Output should contain alpha-beta setting"
    
    print("✓ test_display_performance passed")


def test_thread_safety():
    """Test thread-safe access to settings"""
    print("Testing thread safety...")
    
    manager = SettingsManager()
    results = []
    errors = []
    
    def worker_thread(thread_id):
        try:
            # Each thread tries to get and set settings
            for i in range(10):
                value = manager.get_setting('search_depth')
                success = manager.set_setting('search_depth', (thread_id % 20) + 1)
                results.append((thread_id, i, value, success))
        except Exception as e:
            errors.append(f"Thread {thread_id}: {e}")
    
    # Start multiple threads
    threads = []
    for i in range(5):
        thread = threading.Thread(target=worker_thread, args=(i,))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    assert len(errors) == 0, f"Thread safety errors: {errors}"
    assert len(results) == 50, "Should have 50 results from 5 threads × 10 operations"
    
    print("✓ test_thread_safety passed")


def test_settings_summary():
    """Test get_settings_summary() method"""
    print("Testing settings summary...")
    
    manager = SettingsManager()
    summary = manager.get_settings_summary()
    
    assert isinstance(summary, dict), "Summary should be a dictionary"
    assert 'search_depth' in summary, "Summary should include search_depth"
    
    setting_info = summary['search_depth']
    assert 'name' in setting_info, "Setting info should include name"
    assert 'value' in setting_info, "Setting info should include value"
    assert 'default' in setting_info, "Setting info should include default"
    assert 'range' in setting_info, "Setting info should include range"
    assert 'valid' in setting_info, "Setting info should include valid flag"
    assert 'description' in setting_info, "Setting info should include description"
    
    print("✓ test_settings_summary passed")


def run_all_tests():
    """Run all SettingsManager tests"""
    print("Running SettingsManager unit tests...\n")
    
    test_functions = [
        test_singleton_pattern,
        test_default_settings_loaded,
        test_get_set_setting,
        test_boolean_settings,
        test_float_settings,
        test_invalid_setting_detection,
        test_reset_functionality,
        test_display_performance,
        test_thread_safety,
        test_settings_summary
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
    
    print(f"\nTest Results: {passed}/{len(test_functions)} tests passed")
    
    if failed > 0:
        print(f"⚠️  {failed} tests failed")
        return False
    else:
        print("🎉 All tests passed!")
        return True


if __name__ == "__main__":
    run_all_tests()