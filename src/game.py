import uuid
import time
import os
import json
from src.layout import LayoutRenderer
from src.input_handler import InputHandler
from src.validator import CardValidator
from src.simulator.game_state import GameState
from src.simulator.search import MinimaxSearch
from src.simulator.move_executor import MoveExecutor
from src.simulator.evaluator import PositionEvaluator
from src.config.settings_manager import SettingsManager
from constants import RANK_MAP, SUIT_MAP
from src.settings import MAX_ITERATIONS, SEARCH_DEPTH

class GameManager:
    def __init__(self):
        self.current_game = [[] for _ in range(4)]  # initial deal + 3 reshuffles
        self.saved_games = {}

    def display_settings(self):
        """Display performance settings and return to main menu"""
        settings_manager = SettingsManager()
        settings_manager.display()

        print("\nPress Enter to return to main menu...")
        input()  # Wait for user to press Enter

    def configure_logging_menu(self):
        """Interactive menu for configuring diagnostic logging"""
        settings_manager = SettingsManager()
        current_state = settings_manager.get_setting("logging_enabled")

        print("\n" + "="*50)
        print("DIAGNOSTIC LOGGING CONFIGURATION")
        print("="*50)
        print(f"Current status: {'ENABLED' if current_state else 'DISABLED'}")
        print("\nDiagnostic loggers controlled:")
        print("  • GameState operations")
        print("  • Search algorithms")
        print("  • Move execution")
        print("  • Position evaluation")
        print("\nLog files written to debug/ directory when enabled")

        choice = input(f"\n[E]nable logging, [D]isable logging, or [T]oggle? ").strip().lower()

        if choice == 'e':
            settings_manager.set_setting("logging_enabled", True)
            settings_manager.configure_global_logging()
            print("✓ Diagnostic logging ENABLED")
        elif choice == 'd':
            settings_manager.set_setting("logging_enabled", False)
            settings_manager.configure_global_logging()
            print("✓ Diagnostic logging DISABLED")
        elif choice == 't':
            new_state = settings_manager.toggle_logging()
            print(f"✓ Diagnostic logging {'ENABLED' if new_state else 'DISABLED'}")

        print("\nReturning to main menu...")

    def user_review_layout(self, board, game_id, layout, handler, validator, is_loaded_game=False):
        """Display layout and handle user choice for analyze or edit"""
        print("\nGame layout loaded. Verifying 4-row structure:\n")
        for i in range(4):
            row = board[i * 13:(i + 1) * 13]
            print(f"Row {i+1}: {row}")
        choice = input("\nRun [A]nalysis, [E]dit the layout, or configure [L]ogging? ").strip().lower()

        if choice == 'a':
            self.analyze_layout(layout, handler, validator, game_id)
        elif choice == 'e':
            print("Edit functionality not added yet.")
            exit(0)
        elif choice == 'l':
            self.configure_logging_menu()
            # After configuring logging, offer to run analysis
            run_analysis = input("\nRun analysis with current logging settings? [Y/n]: ").strip().lower()
            if run_analysis != 'n':
                self.analyze_layout(layout, handler, validator, game_id)

    def open_saved_game(self):
        """Load and display a previously saved game"""
        # Check if saves directory exists
        saves_dir = "./saves"
        if not os.path.exists(saves_dir):
            print("No saved games available. The saves directory does not exist.")
            return

        # Get list of .json files
        try:
            files = [f for f in os.listdir(saves_dir) if f.endswith('.json')]
        except OSError:
            print("Error accessing saves directory.")
            return

        if not files:
            print("No saved games available.")
            return

        # Display numbered list of saved games
        print("\nAvailable saved games:")
        for i, filename in enumerate(files, 1):
            game_id = filename[:-5]  # Remove .json extension
            print(f"{i}. {game_id}")

        # Get user selection
        while True:
            try:
                choice = input(f"\nSelect a game (1-{len(files)}): ").strip()
                if not choice:
                    print("Returning to main menu.")
                    return

                selection = int(choice)
                if 1 <= selection <= len(files):
                    selected_file = files[selection - 1]
                    break
                else:
                    print(f"Please enter a number between 1 and {len(files)}.")
            except ValueError:
                print("Please enter a valid number.")

        # Load the selected file
        file_path = os.path.join(saves_dir, selected_file)
        try:
            with open(file_path, 'r') as f:
                board_data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"Error loading saved game: {e}")
            return

        # Validate the loaded data
        if not isinstance(board_data, list) or len(board_data) != 52:
            print("Invalid saved game format. Expected 52 cards.")
            return

        # Extract game_id from filename
        game_id = selected_file[:-5]  # Remove .json extension

        # Create necessary objects
        layout = LayoutRenderer()
        validator = CardValidator()
        handler = InputHandler(layout, validator)

        # Set the current game state
        self.current_game[0] = board_data

        print(f"\nLoaded game: {game_id}")

        # Call user_review_layout with loaded data
        settings_manager = SettingsManager()
        settings_manager.update_manifest_with_game_id(game_id)

        self.user_review_layout(board_data, game_id, layout, handler, validator, is_loaded_game=True)

    def create_new_game(self):
        game_id = input("Enter a Game ID or press Enter to skip: ").strip()
        if not game_id:
            game_id = str(uuid.uuid4())[:8]
            print(f"Generated Game ID: {game_id}")
        else:
            print(f"Using Game ID: {game_id}")

        # Update manifest with game ID if timestamped logging is active
        settings_manager = SettingsManager()
        settings_manager.update_manifest_with_game_id(game_id)

        self.saved_games[game_id] = []
        layout = LayoutRenderer()
        validator = CardValidator()
        handler = InputHandler(layout, validator)

        print("\nStarting initial deal")
        initial_board = handler.collect_card_inputs(game_id=game_id)
        self.current_game[0] = initial_board

        # Use the extracted common functionality
        self.user_review_layout(initial_board, game_id, layout, handler, validator, is_loaded_game=False)

    def analyze_layout(self, layout, handler, validator, game_id):
        """Analyze game layout using GameState representation"""
        print("Initializing GameState analysis...")

        # Get global logging setting
        settings_manager = SettingsManager()
        logging_enabled = settings_manager.get_setting("logging_enabled")

        # Create GameState with diagnostics based on global setting
        game_state = GameState(enable_diagnostics=logging_enabled)

        # Load initial board into GameState
        initial_board = self.current_game[0]
        if not game_state.load_from_flat_board(initial_board):
            print("✗ Failed to load board into GameState")
            return

        print("✓ Board loaded successfully into GameState")

        # Analyze initial position and display moves
        if self._analyze_and_display_moves(game_state, "Initial deal"):
            return

        # Automatically proceed through reshuffles
        for reshuffle_num in range(1, 4):
            print(f"\nProceeding to reshuffle {reshuffle_num}/3...")

            # Temporarily disabled: Get prepopulated cards + positions to skip using GameState immutable sequence detection
            # prev_board = self.current_game[reshuffle_num - 1]
            # skip_cells, prepopulated = self.compute_prepopulated_cells(prev_board)

            # Update handler to show reshuffle number in prompts
            handler.current_reshuffle = reshuffle_num

            # Temporarily disabled prepopulation - collect all cards fresh
            board = handler.collect_card_inputs(game_id=game_id)
            self.current_game[reshuffle_num] = board

            # Reset reshuffle number after collection
            handler.current_reshuffle = None

            # Update GameState with new board and analyze
            if not game_state.load_from_flat_board(board):
                print(f"✗ Failed to load reshuffle {reshuffle_num} into GameState")
                continue

            # Check for win condition and analyze moves
            if self._analyze_and_display_moves(game_state, f"Reshuffle {reshuffle_num}"):
                print(f"\n🎉 Game won after reshuffle {reshuffle_num}!")
                break

        if logging_enabled:
            print("Analysis complete. Diagnostic data saved to debug/ directory")
        else:
            print("Analysis complete.")

    def _analyze_and_display_moves(self, game_state, phase_name):
        """Analyze current position and display optimal move sequence. Returns True if game is won."""
        legal_moves = game_state.get_legal_moves()

        # Check for win condition (no gaps remaining)
        if len(game_state.gaps) == 0:
            print(f"{phase_name}: 🎉 GAME WON! No gaps remaining.")
            return True

        if not legal_moves:
            print(f"{phase_name}: No legal moves available - reshuffle needed")
            return False

        # Get global logging setting for search instance
        settings_manager = SettingsManager()
        logging_enabled = settings_manager.get_setting("logging_enabled")

        # Create search instance to find optimal sequence
        search = MinimaxSearch(enable_diagnostics=logging_enabled)

        # Build optimal move sequence until no more beneficial moves
        move_sequence = []
        move_objects = []
        current_state = game_state
        seen_positions = set()
        prev_immutables = set(current_state.immutable_sequences)
        last_valuable_index = -1  # No valuable moves yet

        for iteration in range(MAX_ITERATIONS):
            position_hash = hash(current_state)
            if position_hash in seen_positions:
                break
            seen_positions.add(position_hash)

            best_move = search.search(current_state, max_depth=SEARCH_DEPTH)
            if not best_move:
                break

            try:
                next_state = search.move_executor.execute_move(current_state, best_move)

                # Check for increase in immutable sequences
                new_immutables = set(next_state.immutable_sequences)
                if len(new_immutables) > len(prev_immutables):
                    last_valuable_index = len(move_sequence)  # This move adds value
                    prev_immutables = new_immutables

                # Record move
                card, (target_row, target_col) = best_move
                card_str = f"{RANK_MAP[card.rank]}{SUIT_MAP[card.suit]}"
                move_sequence.append(f"{card_str} -> R{target_row+1}C{target_col+1}")
                move_objects.append(best_move)

                current_state = next_state

                if len(current_state.gaps) == 0 or not current_state.get_legal_moves():
                    break

            except Exception:
                break
        if move_sequence:
            print(f"{phase_name}: Optimal move sequence:")

            if last_valuable_index >= 0:
                valuable_moves = move_sequence[:last_valuable_index + 1]
                for i in range(0, len(valuable_moves), 3):
                    print(", ".join(valuable_moves[i:i+3]))
                print("No more valuable moves found before next reshuffle.")
            else:
                print("No valuable moves found before next reshuffle.")
        else:
            print(f"{phase_name}: No optimal sequence found")

        return False

    def compute_prepopulated_cells(self, flat_board):
        skip_cells = set()
        prepopulated = {}

        for row_idx in range(4):
            sequence = []
            for col in range(13):
                card = flat_board[row_idx * 13 + col]
                if card == "--" or len(card) != 2:
                    break
                rank, suit = card[0], card[1]

                try:
                    value = self.card_rank_value(rank)
                except ValueError:
                    break

                if value == 2:
                    sequence.append((col, card))
                    continue

                if not sequence:
                    break  # Only start tracking from a 2

                prev_val, prev_suit = self.card_rank_value(sequence[-1][1][0]), sequence[-1][1][1]
                if value == prev_val + 1 and suit == prev_suit:
                    sequence.append((col, card))
                else:
                    break  # Stop if sequence breaks

            for col_idx, card in sequence:
                skip_cells.add((row_idx, col_idx))
                prepopulated[(row_idx, col_idx)] = card

        return skip_cells, prepopulated

    def card_rank_value(self, rank):
        ranks = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7,
                 '8': 8, '9': 9, 'X': 10, 'J': 11, 'Q': 12, 'K': 13}
        r = rank.upper()
        if r not in ranks:
            raise ValueError(f"Invalid rank: {rank}")
        return ranks[r]
