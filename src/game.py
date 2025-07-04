import uuid
import time
from src.layout import LayoutRenderer
from src.input_handler import InputHandler
from src.validator import CardValidator

class GameManager:
    def __init__(self):
        self.current_game = [[] for _ in range(4)]  # initial deal + 3 reshuffles
        self.saved_games = {}

    def open_saved_game(self):
        print("[Stub] Open saved game functionality is not yet implemented.")

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

        print("\nInitial deal complete. Verifying 4-row structure:\n")
        for i in range(4):
            row = initial_board[i * 13:(i + 1) * 13]
            print(f"Row {i+1}: {row}")

        choice = input("\nFinished entering initial deal. [A]nalyze or [E]dit the layout? ").strip().lower()
        if choice == 'a':
            self.analyze_layout(layout, handler, validator, game_id)
        elif choice == 'e':
            print("Edit functionality not added yet.")
            exit(0)

    def analyze_layout(self, layout, handler, validator, game_id):
        """
        Analyze the current game layout using core game state representation and move generator.
        
        This method integrates the GameState and MoveGenerator components to provide
        comprehensive analysis of the current position, including move generation,
        performance metrics, and diagnostic logging.
        
        Args:
            layout: Layout renderer for display
            handler: Input handler for user interaction
            validator: Card validator for input validation  
            game_id: Unique identifier for the game session
        """
        print("Analyzing layout using core game state representation...")
        
        # Import simulator components
        from src.simulator.game_state import create_initial_state
        from src.simulator.move_gen import create_move_generator
        from src.simulator.diagnostics import create_diagnostics, measure_performance
        
        # Convert current board to simulator format
        board_cards = []
        for card in self.current_game[0]:
            if card == "" or card is None:
                board_cards.append("--")
            else:
                board_cards.append(card)
        
        # Create game state with diagnostic logging enabled
        state = create_initial_state(board_cards, enable_diagnostics=True)
        move_gen = create_move_generator(enable_diagnostics=True)
        
        # Generate legal moves
        legal_moves = move_gen.generate_legal_moves(state)
        
        print("Completed analysis. Here are your legal moves:")
        
        if legal_moves:
            for i, move in enumerate(legal_moves):
                print(f"{i+1}. {move.to_compact_string()}")
            
            print(f"\nTotal legal moves: {len(legal_moves)}")
            
            # Performance analysis
            print("\nPerforming performance analysis...")
            diagnostics = create_diagnostics()
            performance_metrics = measure_performance(state, move_gen, iterations=1000)
            diagnostics.log_performance_metrics(performance_metrics, position_count=1000)
            
            total_time = (performance_metrics.hash_generation_time + 
                         performance_metrics.copy_time + 
                         performance_metrics.move_generation_time)
            if total_time > 0:
                positions_per_second = 1000 / total_time
                print(f"Performance: {positions_per_second:.1f} positions/second")
                target_met = "✓" if positions_per_second >= 1000 else "✗"
                print(f"Target (>1000 pos/sec): {target_met}")
        else:
            print("No legal moves available.")
            
            # Check why no moves are available
            gaps = state.get_gaps()
            immutable_positions = state.get_immutable_positions()
            
            print(f"\nDiagnostic information:")
            print(f"- Gaps on board: {len(gaps)}")
            print(f"- Immutable positions: {len(immutable_positions)}")
            
            # Analyze each gap
            for gap_row, gap_col in gaps:
                required_card = move_gen._get_required_card_for_gap(state, gap_row, gap_col)
                if required_card is None:
                    print(f"- Gap R{gap_row+1}C{gap_col+1}: Cannot be filled (King/gap to left)")
                else:
                    card_pos = move_gen._find_card_position(state, required_card)
                    if card_pos is None:
                        print(f"- Gap R{gap_row+1}C{gap_col+1}: Needs {required_card} (not on board)")
                    elif card_pos in immutable_positions:
                        print(f"- Gap R{gap_row+1}C{gap_col+1}: Needs {required_card} (immutable)")
        
        print(f"\nDiagnostic log saved to: debug/gamestate_diagnostics.log")
        print("Review the log file for detailed performance metrics and validation data.")
            print("4C -> R2C4")
            print("XD -> R1C9")
            print("8S -> R4C5")

        reshuffles_remaining = 3
        for reshuffle_num in range(1, 4):
            print(f"\nYou have {reshuffles_remaining} reshuffles remaining.")
            proceed = input("Enter new layout for next [R]eshuffle? ").strip().lower()
            if proceed != 'r':
                print("Exiting reshuffle loop.")
                break

            print(f"\nStarting reshuffle {reshuffle_num}/3")

            # Get prepopulated cards + positions to skip
            prev_board = self.current_game[reshuffle_num - 1]
            skip_cells, prepopulated = self.compute_prepopulated_cells(prev_board)

            board = handler.collect_card_inputs(game_id=game_id, skip_cells=skip_cells, prepopulated_cards=prepopulated)
            self.current_game[reshuffle_num] = board
            reshuffles_remaining -= 1

        print("\nFinal Layout:")
        layout.display_full_board(self.current_game[3])
        print("Ready to begin analyzing.")

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
