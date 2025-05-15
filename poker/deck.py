import random

suits = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']

class Deck:
    def __init__(self):
        self.cards = [{'rank': rank, 'suit': suit} for rank in ranks for suit in suits]
        random.shuffle(self.cards)

    def deal(self, num):
        """Deal a specified number of cards."""
        return [self.cards.pop() for _ in range(num)]
