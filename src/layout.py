class LayoutRenderer:
    def __init__(self):
        self.grid = [["  " for _ in range(13)] for _ in range(4)]
        self.highlights = set()  # Store (row, col) tuples

    def update_cell(self, row, col, value):
        self.grid[row][col] = value

    def highlight_cell(self, row, col):
        self.highlights.add((row, col))

    def clear_highlights(self):
        self.highlights.clear()

    def render(self):
        import sys
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()

        print("** Enter cards as 4c for 4 of clubs\n** Use `x` for 10, `j` for jack, etc.\n** Use `-` or `g` for gap space\n** Use `z` to save and exit\n")
        for r_idx, row in enumerate(self.grid):
            display_row = []
            for c_idx, val in enumerate(row):
                if (r_idx, c_idx) in self.highlights:
                    styled = f"\033[3m\033[31m{val}\033[0m"
                    display_row.append(styled)
                else:
                    display_row.append(val)
            print(" | ".join(display_row))
        print()

    def display_full_board(self, flat_list):
        print("\033[2J\033[H", end="")
        for row in range(4):
            line = []
            for col in range(13):
                value = flat_list[row * 13 + col]
                line.append(value)
            print(" | ".join(line))
