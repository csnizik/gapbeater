from src.game import GameManager

def main():
    print("Welcome to Gaps Solitaire")
    choice = input("Create a [N]ew game or [O]pen a saved game? ").strip().lower()

    game_manager = GameManager()

    if choice == 'o':
        game_manager.open_saved_game()
    else:
        game_manager.create_new_game()

if __name__ == "__main__":
    main()
