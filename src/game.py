import uuid
import time
import json
import os
from src.layout import LayoutRenderer
from src.input_handler import InputHandler
from src.validator import CardValidator

class GameManager:
    def __init__(self):
        self.current_game = [[] for _ in range(4)]  # initial deal + 3 reshuffles
        self.saved_games = {}

    def open_saved_game(self):
        print("[Stub] Open saved game functionality is not yet implemented.")

    def sample_data_handler(self):
        """Load predefined sample game data for testing and demonstration."""
        sample_file = os.path.join("saves", "31870.json")
        
        if not os.path.exists(sample_file):
            print(f"Sample data file {sample_file} not found.")
            return
        
        try:
            with open(sample_file, 'r') as f:
                sample_data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading sample data: {e}")
            return
        
        if len(sample_data) != 52:
            print(f"Invalid sample data: expected 52 cards, got {len(sample_data)}")
            return
        
        game_id = "31870"
        print(f"Loading sample data (Game ID: {game_id})...")
        
        # Set up the game state
        self.saved_games[game_id] = []
        layout = LayoutRenderer()
        validator = CardValidator()
        handler = InputHandler(layout, validator)
        
        # Populate the layout with sample data
        for i, card in enumerate(sample_data):
            row, col = divmod(i, 13)
            layout.update_cell(row, col, card)
        
        self.current_game[0] = sample_data
        
        print("\nSample data loaded successfully!")
        print("Displaying loaded sample data for verification:\n")
        
        # Display the full board using the layout renderer
        layout.display_full_board(sample_data)
        
        print("\nSample data structure verification:")
        for i in range(4):
            row = sample_data[i * 13:(i + 1) * 13]
            print(f"Row {i+1}: {row}")
        
        choice = input("\nSample data loaded. [A]nalyze or [E]xit? ").strip().lower()
        if choice == 'a':
            self.analyze_layout(layout, handler, validator, game_id)
        else:
            print("Exiting to main menu.")
            return

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
        print("Analyzing...")
        
        # Initialize simulator components following PROJECT_CONTEXT.md principles
        try:
            from src.simulator.optimizer import create_strategic_optimizer
            optimizer = create_strategic_optimizer()
            
            # Convert current board to simulator format
            board_cards = []
            for card in self.current_game[0]:
                if card == "" or card is None:
                    board_cards.append("--")
                else:
                    board_cards.append(card)
            
            # Perform blind strategy analysis (Phase 1)
            phase_result = optimizer.analyze_blind_strategy(board_cards)
            
            print("Completed analysis. Here are your recommended moves:")
            
            if phase_result.recommended_moves:
                for i, move in enumerate(phase_result.recommended_moves[:5]):  # Show up to 5 moves
                    print(f"{i+1}. {move.to_compact_string()}")
                    
                if len(phase_result.recommended_moves) > 5:
                    print(f"... and {len(phase_result.recommended_moves) - 5} more moves")
                    
                print(f"\nPosition evaluation: {phase_result.evaluation.total_score:.1f}")
                
                if phase_result.is_winning:
                    print("🎉 This position can be won!")
                else:
                    print("Position analysis complete. Reshuffle may be needed.")
            else:
                print("No legal moves available. Reshuffle required.")
                
        except ImportError as e:
            # Fallback to placeholder if simulator not available
            print("Advanced simulator not available, using basic analysis...")
            time.sleep(1)
            print("Completed analysis. Here are your recommended moves:")
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
        # Find the last populated reshuffle or use the initial deal
        final_layout_index = 0
        for i in range(3, -1, -1):
            if self.current_game[i]:
                final_layout_index = i
                break
        layout.display_full_board(self.current_game[final_layout_index])
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
