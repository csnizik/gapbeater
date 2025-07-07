"""
SettingsManager - Central configuration management for performance tuning.

This module provides a thread-safe, centralized way to manage all configurable
performance parameters in the GapBeater application.
"""

import threading
import time
import logging
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Any, Union, Tuple, Optional
from enum import Enum
from ..settings import (
    SEARCH_DEPTH, SEARCH_TIME_LIMIT, MAX_ITERATIONS, TARGET_SPEED,
    RESPONSE_TIME_LIMIT, MEMORY_LIMIT, ALPHA_BETA_PRUNING, 
    TRANSPOSITION_TABLES, ITERATIVE_DEEPENING, MOVE_ORDERING,
    GAP_CREATION_WEIGHT, SEQUENCE_WEIGHT, ENABLE_DIAGNOSTICS,
    PERFORMANCE_TRACKING
)


class SettingType(Enum):
    """Types of settings for validation and display purposes"""
    INTEGER = "int"
    FLOAT = "float"
    BOOLEAN = "bool"
    STRING = "str"


@dataclass
class SettingDefinition:
    """Definition of a configurable setting"""
    name: str
    description: str
    current_value: Any
    default_value: Any
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    setting_type: SettingType = SettingType.INTEGER
    
    def is_valid(self) -> bool:
        """Check if current value is within valid range"""
        if self.setting_type in [SettingType.INTEGER, SettingType.FLOAT]:
            if self.min_value is not None and self.current_value < self.min_value:
                return False
            if self.max_value is not None and self.current_value > self.max_value:
                return False
        return True
    
    def get_range_str(self) -> str:
        """Get string representation of valid range"""
        if self.setting_type == SettingType.BOOLEAN:
            return "true/false"
        elif self.setting_type == SettingType.STRING:
            return "string"
        elif self.min_value is not None and self.max_value is not None:
            return f"{self.min_value}-{self.max_value}"
        elif self.min_value is not None:
            return f">= {self.min_value}"
        elif self.max_value is not None:
            return f"<= {self.max_value}"
        else:
            return "any"


class SettingsManager:
    """
    Central configuration manager for performance tuning settings.
    
    Provides thread-safe access to all configurable performance parameters
    with validation and display capabilities.
    """
    
    _instance = None
    _lock = threading.RLock()
    
    def __new__(cls):
        """Singleton pattern for centralized settings management"""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        """Initialize settings registry"""
        if self._initialized:
            return
            
        self._settings: Dict[str, SettingDefinition] = {}
        self._lock = threading.RLock()
        self._register_default_settings()
        self._initialized = True
    
    def _register_default_settings(self):
        """Register all default performance settings"""
        
        # Search algorithm settings
        self._settings["search_depth"] = SettingDefinition(
            name="Search Depth",
            description="Maximum depth for minimax search algorithm",
            current_value=SEARCH_DEPTH,
            default_value=SEARCH_DEPTH,
            min_value=1,
            max_value=25,
            setting_type=SettingType.INTEGER
        )
        
        self._settings["max_search_time"] = SettingDefinition(
            name="Search Time Limit",
            description="Maximum time for iterative deepening search (seconds)",
            current_value=SEARCH_TIME_LIMIT,
            default_value=SEARCH_TIME_LIMIT,
            min_value=0.1,
            max_value=30.0,
            setting_type=SettingType.FLOAT
        )
        
        self._settings["max_iterations"] = SettingDefinition(
            name="Max Iterations",
            description="Maximum iterations for search algorithms",
            current_value=MAX_ITERATIONS,
            default_value=MAX_ITERATIONS,
            min_value=1,
            max_value=1000,
            setting_type=SettingType.INTEGER
        )
        
        # Performance target settings
        self._settings["target_positions_per_sec"] = SettingDefinition(
            name="Target Speed",
            description="Target positions evaluated per second",
            current_value=TARGET_SPEED,
            default_value=TARGET_SPEED,
            min_value=1000,
            max_value=1000000,
            setting_type=SettingType.INTEGER
        )
        
        self._settings["max_response_time"] = SettingDefinition(
            name="Response Time Limit",
            description="Maximum acceptable response time (seconds)",
            current_value=RESPONSE_TIME_LIMIT,
            default_value=RESPONSE_TIME_LIMIT,
            min_value=0.1,
            max_value=10.0,
            setting_type=SettingType.FLOAT
        )
        
        self._settings["max_memory_usage"] = SettingDefinition(
            name="Memory Limit",
            description="Maximum memory usage (MB)",
            current_value=MEMORY_LIMIT,
            default_value=MEMORY_LIMIT,
            min_value=10,
            max_value=1000,
            setting_type=SettingType.INTEGER
        )
        
        # Optimization technique toggles
        self._settings["alpha_beta_pruning"] = SettingDefinition(
            name="Alpha-Beta Pruning",
            description="Enable alpha-beta pruning optimization",
            current_value=ALPHA_BETA_PRUNING,
            default_value=ALPHA_BETA_PRUNING,
            setting_type=SettingType.BOOLEAN
        )
        
        self._settings["transposition_tables"] = SettingDefinition(
            name="Transposition Tables",
            description="Enable transposition table caching",
            current_value=TRANSPOSITION_TABLES,
            default_value=TRANSPOSITION_TABLES,
            setting_type=SettingType.BOOLEAN
        )
        
        self._settings["iterative_deepening"] = SettingDefinition(
            name="Iterative Deepening",
            description="Enable iterative deepening search",
            current_value=ITERATIVE_DEEPENING,
            default_value=ITERATIVE_DEEPENING,
            setting_type=SettingType.BOOLEAN
        )
        
        self._settings["move_ordering"] = SettingDefinition(
            name="Move Ordering",
            description="Enable intelligent move ordering",
            current_value=MOVE_ORDERING,
            default_value=MOVE_ORDERING,
            setting_type=SettingType.BOOLEAN
        )
        
        # Evaluator weight constants
        self._settings["gap_creation_weight"] = SettingDefinition(
            name="Gap Creation Weight",
            description="Weight for gap creation in position evaluation",
            current_value=GAP_CREATION_WEIGHT,
            default_value=GAP_CREATION_WEIGHT,
            min_value=0.0,
            max_value=1000.0,
            setting_type=SettingType.FLOAT
        )
        
        self._settings["sequence_weight"] = SettingDefinition(
            name="Sequence Weight",
            description="Weight for sequence building in evaluation",
            current_value=SEQUENCE_WEIGHT,
            default_value=SEQUENCE_WEIGHT,
            min_value=0.0,
            max_value=1000.0,
            setting_type=SettingType.FLOAT
        )
        
        # Logging settings
        self._settings["enable_diagnostics"] = SettingDefinition(
            name="Enable Diagnostics",
            description="Enable detailed diagnostic logging",
            current_value=ENABLE_DIAGNOSTICS,
            default_value=ENABLE_DIAGNOSTICS,
            setting_type=SettingType.BOOLEAN
        )
        
        self._settings["logging_enabled"] = SettingDefinition(
            name="Global Logging",
            description="Master toggle for all diagnostic logging",
            current_value=False,
            default_value=False,
            setting_type=SettingType.BOOLEAN
        )
        
        self._settings["performance_tracking"] = SettingDefinition(
            name="Performance Tracking",
            description="Enable performance metrics tracking",
            current_value=PERFORMANCE_TRACKING,
            default_value=PERFORMANCE_TRACKING,
            setting_type=SettingType.BOOLEAN
        )
    
    def get_setting(self, setting_key: str) -> Any:
        """Get current value of a setting (thread-safe)"""
        with self._lock:
            if setting_key in self._settings:
                return self._settings[setting_key].current_value
            raise KeyError(f"Setting '{setting_key}' not found")
    
    def set_setting(self, setting_key: str, value: Any) -> bool:
        """Set value of a setting with validation (thread-safe)"""
        with self._lock:
            if setting_key not in self._settings:
                raise KeyError(f"Setting '{setting_key}' not found")
                
            setting = self._settings[setting_key]
            
            # Type validation
            expected_type = {
                SettingType.INTEGER: int,
                SettingType.FLOAT: (int, float),  # Allow int for float
                SettingType.BOOLEAN: bool,
                SettingType.STRING: str
            }[setting.setting_type]
            
            if not isinstance(value, expected_type):
                return False
            
            # Convert int to float if needed
            if setting.setting_type == SettingType.FLOAT and isinstance(value, int):
                value = float(value)
            
            # Range validation
            old_value = setting.current_value
            setting.current_value = value
            
            if not setting.is_valid():
                setting.current_value = old_value  # Restore old value
                return False
                
            return True
    
    def reset_setting(self, setting_key: str) -> bool:
        """Reset setting to default value"""
        with self._lock:
            if setting_key not in self._settings:
                return False
            self._settings[setting_key].current_value = self._settings[setting_key].default_value
            return True
    
    def reset_all_settings(self):
        """Reset all settings to default values"""
        with self._lock:
            for setting in self._settings.values():
                setting.current_value = setting.default_value
    
    def get_invalid_settings(self) -> Dict[str, SettingDefinition]:
        """Get all settings with invalid values"""
        with self._lock:
            return {key: setting for key, setting in self._settings.items() 
                   if not setting.is_valid()}
    
    def display(self) -> None:
        """
        Display all settings in a formatted table.
        
        Performance requirement: Must complete in under 100ms.
        """
        start_time = time.perf_counter()
        
        with self._lock:
            # Prepare data for display
            invalid_settings = self.get_invalid_settings()
            settings_data = []
            
            for key, setting in self._settings.items():
                is_invalid = key in invalid_settings
                settings_data.append((setting, is_invalid))
        
        # Format and display table
        print("\n" + "="*80)
        print("PERFORMANCE SETTINGS")
        print("="*80)
        
        # Table headers
        header_format = "{:<25} {:<15} {:<20} {:<18}"
        print(header_format.format("Setting", "Value", "Range", "Description"))
        print("-" * 80)
        
        # Table rows
        row_format = "{:<25} {:<15} {:<20} {:<18}"
        
        for setting, is_invalid in settings_data:
            value_str = str(setting.current_value)
            if is_invalid:
                value_str = f"⚠️  {value_str}"  # Warning indicator
            
            # Truncate description if too long
            description = setting.description
            if len(description) > 17:
                description = description[:14] + "..."
            
            print(row_format.format(
                setting.name,
                value_str,
                setting.get_range_str(),
                description
            ))
        
        # Display warnings for invalid settings
        if invalid_settings:
            print("\n" + "⚠️  WARNINGS:")
            for key, setting in invalid_settings.items():
                print(f"   • {setting.name}: {setting.current_value} is outside valid range {setting.get_range_str()}")
        
        print("="*80)
        
        # Performance tracking
        elapsed_time = time.perf_counter() - start_time
        print(f"Settings displayed in {elapsed_time*1000:.1f}ms")
        
        if elapsed_time > 0.1:  # 100ms requirement
            print("⚠️  Warning: Display took longer than 100ms target")
    
    def get_settings_summary(self) -> Dict[str, Any]:
        """Get summary of all settings for programmatic access"""
        with self._lock:
            return {
                key: {
                    'name': setting.name,
                    'value': setting.current_value,
                    'default': setting.default_value,
                    'range': setting.get_range_str(),
                    'valid': setting.is_valid(),
                    'description': setting.description
                }
                for key, setting in self._settings.items()
            }
    
    def configure_global_logging(self) -> None:
        """
        Configure all diagnostic loggers based on the global logging_enabled setting.
        
        When enabled, sets all diagnostic loggers to DEBUG level and ensures log files
        are rotated (truncated). When disabled, sets loggers to WARNING level.
        """
        logging_enabled = self.get_setting("logging_enabled")
        
        # Define all diagnostic logger names
        diagnostic_loggers = [
            "GameStateDiagnostics",
            "SearchDiagnostics", 
            "MoveExecutorDiagnostics",
            "PositionEvaluatorDiagnostics"
        ]
        
        # Configure log level for all diagnostic loggers
        target_level = logging.DEBUG if logging_enabled else logging.WARNING
        
        for logger_name in diagnostic_loggers:
            logger = logging.getLogger(logger_name)
            logger.setLevel(target_level)
            
            # Update all handlers to the target level
            for handler in logger.handlers:
                handler.setLevel(target_level)
        
        # If logging is being enabled, rotate log files (truncate them)
        if logging_enabled:
            self._rotate_log_files()
    
    def _rotate_log_files(self) -> None:
        """Rotate (truncate) all diagnostic log files to prevent unbounded growth."""
        debug_dir = Path("debug")
        debug_dir.mkdir(exist_ok=True)
        
        log_files = [
            "debug/gamestate_diagnostics.log",
            "debug/search_diagnostics.log",
            "debug/move_executor_diagnostics.log", 
            "debug/position_evaluator_diagnostics.log"
        ]
        
        for log_file in log_files:
            log_path = Path(log_file)
            if log_path.exists():
                # Truncate existing file
                with open(log_path, 'w') as f:
                    f.write("")  # Clear the file
    
    def toggle_logging(self) -> bool:
        """
        Toggle the global logging setting and reconfigure all loggers.
        
        Returns:
            bool: New state of logging (True if now enabled, False if disabled)
        """
        current_state = self.get_setting("logging_enabled")
        new_state = not current_state
        self.set_setting("logging_enabled", new_state)
        self.configure_global_logging()
        return new_state