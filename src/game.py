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
from . import constants

class GameManager:
    def __init__(self):
        self.current_game = [[] for _ in range(4)]  # initial deal + 3 reshuffles
        self.saved_games = {}

    def user_review_layout(self, board, game_id, layout, handler, validator, is_loaded_game=False):
        """Display layout and handle user choice for analyze or edit"""
        print("\nGame layout loaded. Verifying 4-row structure:\n")
        for i in range(4):
            row = board[i * 13:(i + 1) * 13]
            print(f"Row {i+1}: {row}")
        choice = input("\nRun [A]nalysis or [E]dit the layout? ").strip().lower()

        if choice == 'a':
            self.analyze_layout(layout, handler, validator, game_id)
        elif choice == 'e':
            print("Edit functionality not added yet.")
            exit(0)

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
        self.user_review_layout(board_data, game_id, layout, handler, validator, is_loaded_game=True)

    def create_new_game(self):
        game_id = input("Enter a Game ID or press Enter to skip: ").strip()
        if not game_id:
            game_id = str(uuid.uuid4())[:8]
            print(f"Generated Game ID: {game_id}")
        else:
            print(f"Using Game ID: {game_id}")

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

        # Create GameState with diagnostics enabled
        game_state = GameState(enable_diagnostics=True)

        # Load initial board into GameState
        initial_board = self.current_game[0]
        if game_state.load_from_flat_board(initial_board):
            print("✓ Board loaded successfully into GameState")

            # Analyze current position
            legal_moves = game_state.get_legal_moves()
            print(f"Analysis complete. Found {len(legal_moves)} legal moves:")

            # Use search for intelligent move recommendation
            if legal_moves:
                # Create search instance and find best move
                search = MinimaxSearch(enable_diagnostics=True)
                best_move = search.search(game_state, constants.DEFAULT_SEARCH_DEPTH)
                
                if best_move:
                    # Execute the recommended move to get the resulting position for evaluation
                    move_executor = MoveExecutor()
                    evaluator = PositionEvaluator()
                    
                    try:
                        # Get evaluation score for the recommended move
                        new_state = move_executor.execute_move(game_state, best_move)
                        evaluation_score = evaluator.evaluate(new_state)
                        
                        # Display search recommendation
                        card, (target_row, target_col) = best_move
                        card_str = f"{constants.RANK_MAP[card.rank]}{constants.SUIT_MAP[card.suit]}"
                        print(f"  Recommended: {card_str} -> R{target_row+1}C{target_col+1} (score: {evaluation_score:.1f})")
                        
                        # Show performance stats
                        stats = search.get_performance_stats()
                        print(f"  Search evaluated {stats['nodes_searched']} positions in {stats['search_time']:.3f}s")
                        
                    except Exception as e:
                        print(f"  Error evaluating recommended move: {e}")
                        # Fall back to showing basic moves
                        card, (target_row, target_col) = best_move
                        card_str = f"{constants.RANK_MAP[card.rank]}{constants.SUIT_MAP[card.suit]}"
                        print(f"  Recommended: {card_str} -> R{target_row+1}C{target_col+1}")
                
                # Also show other legal moves for context (optional)
                print(f"  Other legal moves:")
                for i, (card, (target_row, target_col)) in enumerate(legal_moves[:5]):  # Show first 5 moves
                    card_str = f"{constants.RANK_MAP[card.rank]}{constants.SUIT_MAP[card.suit]}"
                    print(f"    {card_str} -> R{target_row+1}C{target_col+1}")
            else:
                print("  No legal moves available - reshuffle needed")
        else:
            print("✗ Failed to load board into GameState")
            return

        reshuffles_remaining = 3
        for reshuffle_num in range(1, 4):
            print(f"\nYou have {reshuffles_remaining} reshuffles remaining.")
            proceed = input("Enter new layout for next [R]eshuffle? ").strip().lower()
            if proceed != 'r':
                print("Exiting reshuffle loop.")
                break

            print(f"\nStarting reshuffle {reshuffle_num}/3")

            # Get prepopulated cards + positions to skip using GameState immutable sequence detection
            prev_board = self.current_game[reshuffle_num - 1]
            skip_cells, prepopulated = self.compute_prepopulated_cells(prev_board)

            board = handler.collect_card_inputs(game_id=game_id, skip_cells=skip_cells, prepopulated_cards=prepopulated)
            self.current_game[reshuffle_num] = board

            # Update GameState with new board and analyze
            if game_state.load_from_flat_board(board):
                legal_moves = game_state.get_legal_moves()
                print(f"After reshuffle: {len(legal_moves)} legal moves available")

            reshuffles_remaining -= 1

        print("\nFinal Layout:")
        layout.display_full_board(self.current_game[3])
        print("Analysis complete. Diagnostic data saved to debug/gamestate_diagnostics.log")

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
