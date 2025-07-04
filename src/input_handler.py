import os
import json

class InputHandler:
    def __init__(self, layout_renderer, validator):
        self.layout = layout_renderer
        self.validator = validator
        self.used_cards = set()

    def collect_card_inputs(self, game_id=None, skip_cells=None, prepopulated_cards=None):
        skip_cells = skip_cells or set()
        prepopulated_cards = prepopulated_cards or {}

        cards = [""] * 52  # Flat list of 52 values

        # 🔧 Reset used cards for the new deal
        self.used_cards = set()

        # Pre-fill known cards
        for (r, c), value in prepopulated_cards.items():
            self.layout.update_cell(r, c, value)
            self.used_cards.add(value)
            flat_index = r * 13 + c
            cards[flat_index] = value

        # Clear out non-prepopulated cells
        for index in range(52):
            r, c = divmod(index, 13)
            if (r, c) not in prepopulated_cards:
                self.layout.update_cell(r, c, "  ")
                cards[index] = ""

        # Build list of positions we actually want to collect input for
        input_positions = [
            (r, c) for r in range(4) for c in range(13)
            if (r, c) not in skip_cells
        ]

        current_input_idx = 0
        while current_input_idx < len(input_positions):
            row, col = input_positions[current_input_idx]
            flat_index = row * 13 + col

            self.layout.render()
            user_input = input(f"Row {row+1}, Col {col+1}: ").strip().lower()

            if user_input in {'z'}:
                self.save_partial_game(cards, game_id)
                print(f"\nSaved and exited to saves/{game_id}.json")
                exit(0)

            if not self.validator.is_valid_input(user_input):
                continue

            normalized = self.validator.normalize_input(user_input)

            # Clear any previous highlights before validating
            self.layout.clear_highlights()

            if normalized == "--":
                card_str = "--"
            else:
                if normalized in self.used_cards:
                    for r in range(4):
                        for c in range(13):
                            if self.layout.grid[r][c] == normalized:
                                self.layout.highlight_cell(r, c)
                                break
                    continue

                self.used_cards.add(normalized)
                card_str = normalized

            self.layout.update_cell(row, col, card_str)
            cards[flat_index] = card_str
            current_input_idx += 1

        return cards

    def save_partial_game(self, card_list, game_id):
        os.makedirs("saves", exist_ok=True)
        path = os.path.join("saves", f"{game_id}.json")
        with open(path, "w") as f:
            json.dump(card_list, f)
