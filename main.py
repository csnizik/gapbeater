from src.game import GameManager

def main():
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
