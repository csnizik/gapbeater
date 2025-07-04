import re

class CardValidator:
    GAP_KEYS = {'-', 'g', ' '}
    SUITS = {'c': 'Clubs', 'd': 'Diamonds', 'h': 'Hearts', 's': 'Spades'}
    RANKS = set("23456789xjqk")

    def is_valid_input(self, user_input):
        if len(user_input) != 2:
            return user_input in self.GAP_KEYS
        rank, suit = user_input[0], user_input[1]
        return rank in self.RANKS and suit in self.SUITS

    def normalize_input(self, user_input):
        if user_input in self.GAP_KEYS:
            return "--"
        rank = user_input[0].upper()
        suit = user_input[1].upper()
        return f"{rank}{suit}"
