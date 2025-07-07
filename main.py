import argparse
from src.game import GameManager
from src.config.settings_manager import SettingsManager

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Gaps Solitaire - Interactive card game")
    parser.add_argument("--verbose", action="store_true", 
                       help="Enable verbose diagnostic logging for all components")
    parser.add_argument("--quiet", action="store_true",
                       help="Disable all diagnostic logging (default)")
    args = parser.parse_args()
    
    # Configure global logging based on command line arguments
    settings_manager = SettingsManager()
    if args.verbose:
        settings_manager.set_setting("logging_enabled", True)
        settings_manager.configure_global_logging(create_timestamped_run=True)
        print("Verbose diagnostic logging enabled with timestamped debug directory")
    elif args.quiet:
        settings_manager.set_setting("logging_enabled", False)
        settings_manager.configure_global_logging()
        print("Diagnostic logging disabled")
    
    print("Welcome to Gaps Solitaire")
    choice = input("Create a [N]ew game, [O]pen a saved game, or view [S]ettings? ").strip().lower()

    game_manager = GameManager()

    if choice == 'o':
        game_manager.open_saved_game()
    elif choice == 's':
        game_manager.display_settings()
    else:
        game_manager.create_new_game()

if __name__ == "__main__":
    main()
