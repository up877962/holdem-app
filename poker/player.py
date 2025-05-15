class Player:
    def __init__(self, name):
        self.name = name
        self.chips = 1000
        self.hand = []
        self.status = "active"
        self.has_acted = False
        self.bet_amount = 0  # NEW: Track the current bet amount

    def reset_for_new_game(self):
        """Reset player state for a new hand."""
        self.status = "active"
        self.hand = []
        self.has_acted = False
        self.bet_amount = 0  # Reset bet amount

    def fold(self):
        self.status = "folded"
        self.has_acted = True

    def bet(self, amount):
        self.chips -= amount
        self.bet_amount += amount  # Track total bet for matching calls
        self.has_acted = True
        return amount
