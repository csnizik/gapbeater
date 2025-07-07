"""
SettingsManager - Central configuration management for performance tuning.

This module provides a thread-safe, centralized way to manage all configurable
performance parameters in the GapBeater application.
"""

import threading
import time
import logging
import json
from datetime import datetime
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
        self._current_run_id = None  # Track current run for timestamped logging
        self._current_game_id = None  # Track current game ID
        self._pending_timestamped_run = False  # Flag for deferred directory creation
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
    
    def configure_global_logging(self, create_timestamped_run: bool = False) -> None:
        """
        Configure all diagnostic loggers based on the global logging_enabled setting.
        
        When enabled, sets all diagnostic loggers to DEBUG level and ensures log files
        are rotated (truncated). When disabled, sets loggers to WARNING level.
        
        Args:
            create_timestamped_run: If True, marks that we want timestamped logging 
                                   (actual directory creation deferred until game_id available)
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
        
        # If logging is being enabled, set up logging directory structure
        if logging_enabled:
            if create_timestamped_run:
                # Mark that we want timestamped logging but defer creation until game_id available
                self._pending_timestamped_run = True
            else:
                self._rotate_log_files()
    
    def _setup_timestamped_run(self, game_id: str) -> None:
        """Create timestamped subdirectory for this run and generate manifest.
        
        Args:
            game_id: The game ID to group runs under
        """
        # Generate timestamp in format YYYYMMDDHHMM
        timestamp = datetime.now().strftime("%Y%m%d%H%M")
        self._current_run_id = timestamp
        self._current_game_id = game_id
        
        # Create directory structure: debug/{game_id}/{timestamp}/
        run_dir = Path(f"debug/{game_id}/{timestamp}")
        run_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate and save manifest
        self._generate_manifest(run_dir)
        
        # Update log file paths to use timestamped directory
        self._setup_timestamped_log_files(run_dir)
    
    def _generate_manifest(self, run_dir: Path) -> None:
        """Generate manifest file with all runtime metadata."""
        manifest_data = {
            "run_metadata": {
                "timestamp": datetime.now().isoformat(),
                "run_id": self._current_run_id,
                "format_version": "1.0"
            },
            "performance_settings": {
                # Core search algorithm settings
                "SEARCH_DEPTH": self.get_setting("search_depth"),
                "SEARCH_TIME_LIMIT": self.get_setting("max_search_time"), 
                "MAX_ITERATIONS": self.get_setting("max_iterations"),
                
                # Performance targets
                "TARGET_SPEED": self.get_setting("target_positions_per_sec"),
                "RESPONSE_TIME_LIMIT": self.get_setting("max_response_time"),
                "MEMORY_LIMIT": self.get_setting("max_memory_usage"),
                
                # Optimization toggles
                "ALPHA_BETA_PRUNING": self.get_setting("alpha_beta_pruning"),
                "TRANSPOSITION_TABLES": self.get_setting("transposition_tables"),
                "ITERATIVE_DEEPENING": self.get_setting("iterative_deepening"),
                "MOVE_ORDERING": self.get_setting("move_ordering"),
                
                # Evaluation weights
                "GAP_CREATION_WEIGHT": self.get_setting("gap_creation_weight"),
                "SEQUENCE_WEIGHT": self.get_setting("sequence_weight")
            },
            "additional_performance_factors": {
                # Board configuration (affects search space)
                "BOARD_ROWS": 4,
                "BOARD_COLS": 13,
                "DECK_SIZE": 52,
                
                # Position evaluator constants (affect scoring)
                "CORRECT_PLACEMENT_WEIGHT": 50.0,
                "DEAD_GAP_PENALTY": -5.0,
                "BASE_SCORE": 50.0,
                "NORMALIZATION_FACTOR": 100.0,
                
                # Zobrist hashing configuration (affects transposition tables)
                "ZOBRIST_SEED": 12345,
                "ZOBRIST_BITS": 64,
                
                # Game state caching
                "HASH_TABLE_ENABLED": self.get_setting("transposition_tables"),
                
                # Logging configuration
                "ENABLE_PERFORMANCE_TRACKING": self.get_setting("performance_tracking"),
                "GLOBAL_LOGGING_ENABLED": self.get_setting("logging_enabled")
            },
            "runtime_environment": {
                "python_version": f"{__import__('sys').version_info.major}.{__import__('sys').version_info.minor}.{__import__('sys').version_info.micro}",
                "platform": __import__('platform').platform(),
                "processor": __import__('platform').processor() or "unknown"
            }
        }
        
        # Add game_id if we can determine it (placeholder for now)
        # This would be populated if we have access to the current game instance
        manifest_data["game_session"] = {
            "game_id": self._current_game_id or "TBD",  # Use current game ID if available
            "session_start": datetime.now().isoformat()
        }
        
        # Write manifest as JSON
        manifest_path = run_dir / "manifest.json"
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest_data, f, indent=2, ensure_ascii=False)
    
    def _setup_timestamped_log_files(self, run_dir: Path) -> None:
        """Configure log files to write to timestamped directory."""
        # This will be used by diagnostic classes when they're initialized
        # For now, we'll store the path for future use
        self._current_log_dir = run_dir
    
    def get_current_log_directory(self) -> Optional[Path]:
        """Get the current timestamped log directory if one exists."""
        return getattr(self, '_current_log_dir', None)
    
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
    
    def setup_timestamped_run_with_game_id(self, game_id: str) -> None:
        """
        Create timestamped run directory if one was requested via --verbose flag.
        
        Args:
            game_id: The game ID to use for directory structure
        """
        if self._pending_timestamped_run and self.get_setting("logging_enabled"):
            self._setup_timestamped_run(game_id)
            self._pending_timestamped_run = False
    
    def update_manifest_with_game_id(self, game_id: str) -> None:
        """Update the manifest file with the actual game ID once it's available."""
        # If we have a pending timestamped run, create it now
        self.setup_timestamped_run_with_game_id(game_id)
        
        # If we already have a timestamped run, update its manifest
        if not hasattr(self, '_current_run_id') or not self._current_run_id:
            return
            
        run_dir = Path(f"debug/{game_id}/{self._current_run_id}")
        manifest_path = run_dir / "manifest.json"
        
        if not manifest_path.exists():
            return
            
        try:
            # Read existing manifest
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest_data = json.load(f)
            
            # Update game_id
            manifest_data["game_session"]["game_id"] = game_id
            
            # Write back to file
            with open(manifest_path, 'w', encoding='utf-8') as f:
                json.dump(manifest_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            # Log error but don't fail the application
            print(f"Warning: Could not update manifest with game ID: {e}")
    
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